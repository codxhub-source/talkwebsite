# core/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.http import JsonResponse
from django.utils.dateformat import format as date_format
from django.utils import timezone
import json

from .forms import SignUpForm, LoginForm, ProfileEditForm
from .models import User
from django.db.models import Q
import random
from .models import Conversation, Message
from .forms import MessageForm
from django.shortcuts import reverse
from django.core.paginator import Paginator
from django.core.cache import cache
from django.utils import timezone





    
@login_required
def update_typing_status(request, conversation_id):
    """Update the typing status of a user in a conversation"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            is_typing = data.get('is_typing', False)
            snippet = data.get('snippet', '')
            
            conversation = get_object_or_404(
                Conversation.objects.filter(participants=request.user), 
                pk=conversation_id
            )
            
            if is_typing:
                conversation.typing_users.add(request.user)
            else:
                conversation.typing_users.remove(request.user)
            
            typing_users = conversation.get_typing_users(exclude_user=request.user)
            result = []
            for user in typing_users:
                result.append({
                    'id': user.id,
                    'username': user.username,
                    'photo': user.photo.url if getattr(user, 'photo', None) else '',
                })

            return JsonResponse({'status': 'ok', 'typing_users': result})
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
            
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)


@login_required
def get_typing_users(request, conversation_id):
    """Get the list of users currently typing in a conversation"""
    conversation = get_object_or_404(
        Conversation.objects.filter(participants=request.user), 
        pk=conversation_id
    )
    typing_users = conversation.get_typing_users(exclude_user=request.user)
    result = []
    for user in typing_users:
        result.append({
            'id': user.id,
            'username': user.username,
            'photo': user.photo.url if getattr(user, 'photo', None) else '',
        })

    return JsonResponse({'status': 'ok', 'typing_users': result})


@login_required
def conversation_statuses(request, conversation_id):
    """Return online status for participants in a conversation."""
    conv = get_object_or_404(Conversation.objects.filter(participants=request.user), pk=conversation_id)
    participants = conv.participants.all()
    statuses = []
    now = timezone.now()
    for u in participants:
        if not u.last_activity:
            status = 'offline'
        else:
            delta = now - u.last_activity
            if delta.total_seconds() < 300:
                status = 'online'
            elif delta.total_seconds() < 900:
                status = 'away'
            else:
                status = 'offline'
        statuses.append({'id': u.id, 'username': u.username, 'status': status})

    return JsonResponse({'status': 'ok', 'participants': statuses})


def home(request):
    """
    Renders the home page.
    """
    return render(request, 'home.html')

@login_required
def logout_view(request):
    """Log out the current user and redirect to login page.
    
    Shows success message and accepts both GET and POST methods.
    """
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('login')


# Registration view (GET shows form, POST processes it)
@require_http_methods(["GET", "POST"])
def signup_view(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            # age check is enforced in SignUpForm.clean_age
            user = form.save(commit=False)
            user.save()
            login(request, user)
            return redirect("home")
    else:
        form = SignUpForm()
    return render(request, "core/signup.html", {"form": form})


# Login view (wrap default behavior to prevent under-18 logins)
@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            # double-check age after authentication
            if not user.is_adult():
                # Add an error to the form so it appears on the page
                form.add_error(None, "Your account indicates you are under 18. Access denied.")
            else:
                login(request, user)
                return redirect("home")
    else:
        form = LoginForm(request)
    return render(request, "core/login.html", {"form": form})


# Simple home — show some links (requires login)
@login_required
def home(request):
    # Show a short list of opposite-gender users to quickly start conversations
    me = request.user
    opp_gender = me.opposite_gender()
    opposites = User.objects.filter(gender=opp_gender).exclude(pk=me.pk)[:5]
    return render(request, "core/home.html", {"opposites": opposites})


# Search opposite gender users (requires login)
@login_required
def search_opposite(request):
    me = request.user
    opp_gender = me.opposite_gender()
    q = request.GET.get("q", "").strip()
    users = User.objects.filter(gender=opp_gender).exclude(pk=me.pk)
    if q:
        users = users.filter(Q(username__icontains=q) | Q(email__icontains=q))
    return render(request, "core/search.html", {"users": users, "q": q})


# Profile views
@login_required
def profile_detail(request, pk):
    profile = get_object_or_404(User, pk=pk)
    return render(request, "core/profile_detail.html", {"profile": profile})


@login_required
def profile_edit(request):
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile_detail', pk=request.user.pk)
    else:
        form = ProfileEditForm(instance=request.user)
    return render(request, 'core/profile_edit.html', {'form': form})



# Random opposite profile
@login_required
def random_profile(request):
    me = request.user
    opp_gender = me.opposite_gender()
    candidates = list(User.objects.filter(gender=opp_gender).exclude(pk=me.pk))
    profile = random.choice(candidates) if candidates else None
    return render(request, "core/random.html", {"profile": profile})


@login_required
def users_by_gender(request, gender):
    """List users filtered by gender (M or F). Paginated and excludes current user."""
    gender = gender.upper()
    if gender not in dict(User.GENDER_CHOICES):
        messages.error(request, "Invalid gender filter.")
        return redirect('home')

    users_qs = User.objects.filter(gender=gender).exclude(pk=request.user.pk)
    paginator = Paginator(users_qs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'core/users_by_gender.html', {'page_obj': page_obj, 'gender': gender})


# Message management
@login_required
def delete_message(request, message_id):
    message = get_object_or_404(Message, id=message_id, sender=request.user)
    message.is_deleted = True
    message.save()
    return JsonResponse({'status': 'ok'})


@login_required
def edit_message(request, message_id):
    message = get_object_or_404(Message, id=message_id, sender=request.user)
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_content = data.get('content', '').strip()
            if new_content:
                message.content = new_content
                message.edited_at = timezone.now()
                message.save()
                return JsonResponse({
                    'status': 'ok',
                    'message': {
                        'content': message.content,
                        'edited_at': date_format(message.edited_at, 'g:i A')
                    }
                })
            return JsonResponse({'status': 'error', 'message': 'Content cannot be empty'}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)


# Conversations and messaging
@login_required
def conversations_list(request):
    conversations = request.user.conversations.all().prefetch_related('participants')
    # Annotate each conversation with the other participant before rendering
    conversations_with_other = []
    for conv in conversations:
        conv.other_participant = conv.other_participant(request.user)
        conversations_with_other.append(conv)
    return render(request, 'core/conversation_list.html', {'conversations': conversations_with_other})


@login_required
def start_conversation(request, pk):
    """Start (or open) a conversation between request.user and user with id=pk."""
    other = get_object_or_404(User, pk=pk)
    if other == request.user:
        return redirect('profile_detail', pk=pk)

    # Try to find an existing conversation with exactly these two participants
    conv = Conversation.objects.filter(participants=request.user).filter(participants=other).distinct().first()
    if conv is None:
        conv = Conversation.objects.create()
        conv.participants.add(request.user, other)
    return redirect('conversation_detail', pk=conv.pk)


@login_required
def conversation_detail(request, pk):
    conv = get_object_or_404(Conversation, pk=pk)
    if not conv.participants.filter(pk=request.user.pk).exists():
        messages.error(request, "You are not a participant in that conversation.")
        return redirect('home')

    # When a user opens the conversation (GET), mark incoming unread messages as read
    if request.method == 'GET':
        Message.objects.filter(conversation=conv, read=False).exclude(sender=request.user).update(read=True)

    if request.method == 'POST':
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            try:
                data = json.loads(request.body)
                form = MessageForm({'content': data.get('content', '')})
                if form.is_valid():
                    # Prevent sending if any other participant has blocked the sender
                    other_participants = conv.participants.exclude(pk=request.user.pk)
                    for oth in other_participants:
                        if oth.blocked_users.filter(pk=request.user.pk).exists():
                            return JsonResponse({'status': 'error', 'message': 'You are blocked by this user. Message not sent.'}, status=403)

                    msg = form.save(commit=False)
                    msg.conversation = conv
                    msg.sender = request.user
                    msg.save()
                    return JsonResponse({
                        'status': 'ok',
                        'message': {
                            'id': msg.id,
                            'content': msg.content,
                            'timestamp': date_format(msg.timestamp, 'g:i A'),
                            'sender': msg.sender.username,
                            'is_mine': True
                        }
                    })
                return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
            except json.JSONDecodeError:
                return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        else:
            form = MessageForm(request.POST)
            if form.is_valid():
                # Prevent sending if any other participant has blocked the sender
                other_participants = conv.participants.exclude(pk=request.user.pk)
                for oth in other_participants:
                    if oth.blocked_users.filter(pk=request.user.pk).exists():
                        messages.error(request, 'You are blocked by this user. Message not sent.')
                        return redirect(reverse('conversation_detail', kwargs={'pk': conv.pk}))

                msg = form.save(commit=False)
                msg.conversation = conv
                msg.sender = request.user
                msg.save()
                return redirect(reverse('conversation_detail', kwargs={'pk': conv.pk}))
    else:
        form = MessageForm()

    messages_qs = conv.messages.select_related('sender')
    
    # IDs of users the current user has blocked (for template checks)
    blocked_ids = list(request.user.blocked_users.values_list('id', flat=True)) if request.user.is_authenticated else []

    return render(request, 'core/conversation_detail.html', {
        'conversation': conv,
        'conversation_messages': messages_qs,
        'form': form,
        'blocked_ids': blocked_ids,
    })


@login_required
@require_http_methods(["POST"])
def block_user(request, pk):
    """Toggle blocking of a user. Returns JSON {'status':'blocked'|'unblocked'}"""
    target = get_object_or_404(User, pk=pk)
    if target == request.user:
        return JsonResponse({'status': 'error', 'message': 'Cannot block yourself'}, status=400)

    if target in request.user.blocked_users.all():
        request.user.blocked_users.remove(target)
        return JsonResponse({'status': 'unblocked'})
    else:
        request.user.blocked_users.add(target)
        return JsonResponse({'status': 'blocked'})


@login_required
@require_http_methods(["GET", "POST"])
def account_delete(request):
    """Show a confirmation page (GET) and delete the authenticated user's account on POST.
    
    After deletion the user is logged out and redirected to signup page.
    """
    if request.method == 'POST':
        # Delete the user account safely
        user = request.user
        # Log out first to clear session
        logout(request)
        username = user.username
        user.delete()
        messages.success(request, f"Account '{username}' deleted. Create a new account to continue.")
        return redirect('signup')

    return render(request, 'core/account_confirm_delete.html')

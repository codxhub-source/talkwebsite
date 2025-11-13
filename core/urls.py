from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup_view, name='signup'),
    path('accounts/login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('account/delete/', views.account_delete, name='account_delete'),
    path('search/', views.search_opposite, name='search'),
    path('random/', views.random_profile, name='random'),
    path('profile/<int:pk>/', views.profile_detail, name='profile_detail'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('users/gender/<str:gender>/', views.users_by_gender, name='users_by_gender'),
]

# Conversations and Messages
urlpatterns += [
    path('conversations/', views.conversations_list, name='conversations_list'),
    path('conversations/<int:pk>/', views.conversation_detail, name='conversation_detail'),
    path('start-conversation/<int:pk>/', views.start_conversation, name='start_conversation'),
    path('messages/<int:message_id>/delete/', views.delete_message, name='delete_message'),
    path('messages/<int:message_id>/edit/', views.edit_message, name='edit_message'),
    path('conversations/<int:conversation_id>/typing/', views.update_typing_status, name='update_typing_status'),
    path('conversations/<int:conversation_id>/typing-users/', views.get_typing_users, name='get_typing_users'),
    path('conversations/<int:conversation_id>/statuses/', views.conversation_statuses, name='conversation_statuses'),
    path('users/<int:pk>/block/', views.block_user, name='block_user'),
    
]
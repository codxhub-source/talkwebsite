from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User
from django import forms
from .models import Message


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('photo', 'bio', 'email')
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'})
        }


class SignUpForm(UserCreationForm):
    gender = forms.ChoiceField(
        choices=User.GENDER_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label="Gender"
    )
    age = forms.IntegerField(
        min_value=0,
        max_value=120,
        label="Age",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ['username', 'email', 'password1', 'password2']:
            self.fields[field_name].widget.attrs['class'] = 'form-control'

    class Meta:
        model = User
        fields = ('username', 'email', 'gender', 'age', 'password1', 'password2')

    def clean_age(self):
        """Prevent users under 18 from signing up"""
        age = self.cleaned_data.get('age')
        if age is None or age < 18:
            raise forms.ValidationError("You must be at least 18 years old to use this site.")
        return age


class LoginForm(AuthenticationForm):
    """We check age restriction after authentication in the view"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your username'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ('content',)
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '2',
                'placeholder': 'Write a message...',
                'style': 'resize: none;'
            })
        }

    def clean_content(self):
        content = (self.cleaned_data.get('content') or '').strip()
        if not content:
            raise forms.ValidationError('Message cannot be empty.')
        if len(content) > 1000:  # Reasonable limit for a chat message
            raise forms.ValidationError('Message is too long (max 1000 characters).')
        return content

from django import forms
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import get_user_model, forms as auth_forms
from .models import Thread, Post


message = 'Username must consist of only lowercase or uppercase letters, numbers, ' \
          'or _@+.- characters'
validate_username_chars = RegexValidator(regex=r'^[a-zA-Z0-9_+.@-]+$', message=message)
def validate_username_unique(username):
    try:
        get_user_model().objects.get(username=username)
    except ObjectDoesNotExist:
        return
    else:
        raise ValidationError(_('Username already exists'), code='exists')

def validate_thread_title_unique(title):
    try:
        Thread.objects.get(thread_title=title)
    except ObjectDoesNotExist:
        return
    else:
        raise ValidationError(_('Thread with that name already exists'), code='exists')


# def validate_post_unique(post):
#     try:
#         Post.objects.get(full_text=post)
#         Thread.objects.get(full_text=post)
#     except ObjectDoesNotExist:
#         return
#     else:
#         raise ValidationError(_('You cannot copy another user\'s post'), code='exists')


class AuthenticationFormSub(auth_forms.AuthenticationForm):
    def confirm_login_allowed(self, user):
        pass


class Registration(forms.Form):
    username = forms.CharField(max_length=20, min_length=1, validators=[
        validate_username_chars, validate_username_unique
    ])
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField()
    def clean(self):
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')
        if password and confirm_password:
            if password != confirm_password:
                error = ValidationError(_('Passwords don\'t match'), code='match')
                self.add_error('password', error)


class NewThread(forms.Form):
    thread_title = forms.CharField(max_length=150, min_length=1, label='Title',
                                   validators=[validate_thread_title_unique])
    full_text = forms.CharField(widget=forms.Textarea, label='Text')


class Post(forms.Form):
    full_text = forms.CharField(widget=forms.Textarea, label='Add new post',
                                min_length=1)


class File(forms.Form):
    upload_file = forms.ImageField(max_length=300)


class Info(forms.Form):
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    signature = forms.CharField(widget=forms.Textarea, required=False)


class Email(forms.Form):
    new_email = forms.EmailField(help_text='The confirmation mail will be sent to this address.')

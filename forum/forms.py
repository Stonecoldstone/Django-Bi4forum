from django import forms
from django.contrib.auth import forms as auth_forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import \
    password_validators_help_texts as pswd_help
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.validators import RegexValidator
from django.utils.translation import ugettext_lazy as _

from . import settings as forum_settings
from .models import Post, SubForum, Thread
from .widgets import ForumWidget

message = _('Username must consist of only lowercase or uppercase letters, numbers, '
            'or _@+.- characters.')
validate_username_chars = RegexValidator(regex=r'^[a-zA-Z0-9_+.@-]+$', message=message)


def validate_username_unique(username):
    try:
        get_user_model().objects.get(username=username)
    except ObjectDoesNotExist:
        return
    else:
        raise ValidationError(_('Username already exists.'), code='exists')


def validate_thread_title_unique(title):
    try:
        Thread.objects.get(thread_title=title)
    except ObjectDoesNotExist:
        return
    else:
        raise ValidationError(_('Thread with that name already exists.'), code='exists')


def validate_avatar(file):
    content_type = file.content_type.split('/')[0]
    if content_type != 'image':
        raise ValidationError(_('File is not an image'), code='wrong_type')
    if file.size > forum_settings.FILE_MAX_SIZE:
        raise ValidationError(_('File size should be less than 1 MB'), code='size_limit')
    return


class AuthenticationFormSub(auth_forms.AuthenticationForm):
    def confirm_login_allowed(self, user):
        pass


class Registration(auth_forms.UserCreationForm):
    username = forms.CharField(max_length=20, min_length=1,
                               label=_('* Username'),
                               help_text=_('Username that will be displayed on forum and'
                                           ' used for authentication.\n'
                                           'May contain 1-20 letters, numbers,'
                                           ' and _@+.- characters'),
                               validators=[
                                   validate_username_chars,
                                   validate_username_unique
                               ])
    email = forms.EmailField(label='* Email')
    password1 = forms.CharField(label=_('* Password'),
                                strip=False,
                                widget=forms.PasswordInput,
                                help_text='\n'.join(pswd_help()))
    password2 = forms.CharField(label=_('* Password confirmation'),
                                widget=forms.PasswordInput,
                                strip=False,
                                help_text=_("Enter the same password as before, for verification."))

    class Meta:
        model = get_user_model()
        fields = [
            'username', 'email', 'password1', 'password2', 'first_name',
            'last_name'
        ]


class NewThread(forms.ModelForm):
    thread_title = forms.CharField(max_length=70, min_length=1, label='Title',
                                   validators=[validate_thread_title_unique])
    full_text = forms.CharField(widget=ForumWidget(attrs={'rows': '12'}), label='Text', min_length=1)
    class Meta:
        model = Thread
        fields = ['thread_title', 'full_text']


class NewThreadEdit(NewThread):
    thread_title = forms.CharField(max_length=70, min_length=1, label='Title')


class Post(forms.ModelForm):
    full_text = forms.CharField(widget=ForumWidget(attrs={'rows': '12'}), label='',
                                min_length=1)

    class Meta:
        model = Post
        fields = ['full_text']


class File(forms.Form):
    upload_file = forms.ImageField(max_length=200, validators=[validate_avatar])


class Info(forms.Form):
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    signature = forms.CharField(max_length=500, widget=ForumWidget(attrs={'rows': '12'}), required=False)


class Email(forms.Form):
    new_email = forms.EmailField(help_text='The confirmation mail will be sent to this address.')


# SUBFORUMS_CHOICES = [(sub.id, sub.title) for sub in SubForum.objects.all()]
# SEARCH_BY_CHOICES = [
#     ('pt', 'Posts, threads and titles'),
#     ('p', 'Only posts'),
#     ('t', 'Only thread titles'),
# ]
SORT_BY_CHOICES = [
    ('r', 'Relevance'),
    ('p', 'Publication Date'),
    ('rt', 'Rating')
]

class Search(forms.Form):
    search = forms.CharField(max_length=50, required=False)
    user = forms.CharField(max_length=20, required=False)
    subforums = forms.ModelMultipleChoiceField(required=False,
                                               queryset=SubForum.objects.all(),
                                               help_text=
                                               'Hold "Ctrl" or "Shift" to'
                                               ' select multiple subforums'
                                               ' or to remove selection')
    only_threads = forms.BooleanField(label='Search by first posts only', required=False)
    sort_by = forms.ChoiceField(choices=SORT_BY_CHOICES, initial='r',
                                widget=forms.RadioSelect)

    def clean(self):
        super(Search, self).clean()
        search = self.cleaned_data.get('search')
        user = self.cleaned_data.get('user')
        if not search and not user:
            raise ValidationError(_('Enter either a search string or username.'),
                                  code='empty_search')


class PasswordChange(auth_forms.PasswordChangeForm):
    new_password1 = forms.CharField(label=_("New password"),
                                    widget=forms.PasswordInput,
                                    strip=False,
                                    help_text='\n'.join(pswd_help()))

import io

from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.files import File
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from PIL import Image

from . import settings as forum_settings


def resize(size, prefix='', img=None, bytes=None):
    if img:
        image = Image.open(img)
    else:
        file = io.BytesIO(bytes)
        image = Image.open(file)
    w, h = image.size
    pref_w, pref_h = size
    new_size = (w / h) * pref_h, pref_h
    if new_size[0] < pref_w or new_size[1] < pref_h:
        new_size = pref_w, (h / w) * pref_w
    new_size = tuple(round(i) for i in new_size)
    image = image.resize(new_size, Image.ANTIALIAS)
    w, h = new_size
    a, b = ((w - pref_w) / 2), ((h - pref_h) / 2)
    box = (a, b, w - a, h - b)
    image = image.crop(box)
    if img:
        file = '%s%s' % (prefix, img)
    else:
        file = io.BytesIO()
        image.save(file, format='JPEG')
        file.seek(0)
    return file


def handle_avatar(uploaded_file, filefield, size):
    resized_img = resize(size, bytes=uploaded_file.read())
    filefield.delete(save=False)
    name = uploaded_file.name
    file = File(resized_img)
    filefield.save(name, file)




def is_auth(user):
    return not user.is_authenticated()


def active(user):
    return user.is_active


def not_active(user):
    return not user.is_active


class EmailTokenGenerator(PasswordResetTokenGenerator):

    def _make_hash_value(self, user, timestamp):
        if not user.is_active:
            email = user.email
        else:
            email = user.userprofile.new_email
        login_timestamp = '' if user.last_login is None else user.last_login.replace(microsecond=0, tzinfo=None)
        return (str(user.pk) + str(user.is_active) +
                email + str(login_timestamp) + str(timestamp))


def send_confirmation(request, user, email,
                      subject_template='registration/email_subject.html',
                      message_template='registration/email_body.html'):
    token = EmailTokenGenerator().make_token(user)
    link = request.build_absolute_uri(reverse('forum:email_confirmation',
                                              args=(user.id, token)))
    message_context = {
        'username': user.username, 'forum_name': forum_settings.FORUM_NAME, 'link': link,
    }
    subject_context = {
        'forum_name': forum_settings.FORUM_NAME
    }
    subject = render_to_string(subject_template, subject_context)
    message = render_to_string(message_template, message_context)
    send_mail(subject, message, settings.EMAIL_HOST_USER,
              [email], fail_silently=False)

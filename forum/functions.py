import math
import io
from PIL import Image
from django.core.files import File
import random
from .models import UserKey
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
import sys

def pages(content_on_page, page_num, content_num):
    index = page_num * content_on_page
    previndex = (page_num - 1) * content_on_page
    range_val = math.ceil((content_num / content_on_page) + 1)
    page_list = list(range(1, range_val)) or [1]
    return index, previndex, page_list


def resize(size, prefix='', img=None, bytes=None):
    try:
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
        region = image.crop(box)
        if img:
            file = '%s%s' % (prefix, img)
        else:
            file = io.BytesIO()
            region.save(file, format='JPEG')
            file.seek(0)
        return file
    except IOError:
        return


def handle_avatar(uploaded_file, filefield, size):
    resized_img = resize(size, bytes=uploaded_file.read())
    if resized_img:
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

default_msg = '''
    Dear %(username)s,
    In order to complete registration at %(forum_name)s and activate your account,
    you need to follow the link below:
    %(link)s
    '''

email_change_msg = '''
    Dear %(username)s,
    To validate your new email, you need to follow the link below:
    %(link)s
'''

def send_confirmation(request, user, email=None, message=default_msg):
    key = random.SystemRandom().getrandbits(32)
    try:
        key_model = UserKey.objects.get(user=user)
        key_model.key = key
    except ObjectDoesNotExist:
        key_model = UserKey(user=user, key=key)
    key_model.save()
    msg_dict = {
        'username': user.username, 'forum_name': settings.FORUM_NAME,
        'link': request.build_absolute_uri(reverse('forum:email_confirmation', args=(user.id, key)))
    }
    message = message % msg_dict
    subject = '%s | Email confirmation' % settings.FORUM_NAME
    if email is None:
        email = user.email
    send_mail(subject, message, settings.EMAIL_HOST_USER, [email], fail_silently=False)



# functions for email confirmation:
# def activate_account(user):
#




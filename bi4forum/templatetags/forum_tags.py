from django import template
import re
from django.utils import html
from django.utils.safestring import mark_safe
from django.db.models import Count
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
import math

register = template.Library()

def size_repl(match):
    content = match.group('content')
    size = match.group('size')
    try:
        size = int(size)
        if 9 < size < 41:
            repl = r'<span style="font-size:%dpx">%s</span>' % (size, content)
            return repl
        else:
            raise ValueError
    except ValueError:
        return content


def color_repl(match):
    color_list = ['red', 'green', 'blue', 'white', 'orange', 'purple', 'black']
    color = match.group('color')
    content = match.group('content')
    if color in color_list:
        repl = r'<span style="color:%s">%s</span>' % (color, content)
    else:
        repl = content
    return repl

reg_list = [
        [r'\[b\](?P<content>.*?)\[/b\]', r'<b>\g<content></b>'],
        [r'\[i\](?P<content>.*?)\[/i\]', r'<i>\g<content></i>'],
        [
            r'\[lt\](?P<content>.*?)\[/lt\]',
            r'<span style="text-decoration:line-through">\g<content></span>'
        ],
        [
            r'\[u\](?P<content>.*?)\[/u\]',
            r'<span style="text-decoration:underline">\g<content></span>'
        ],
        [r'\[center\](?P<content>.*?)\[/center\]', r'<p style="text-align:center">\g<content></p>'],
        [r'\[a=(?P<href>.*?)\](?P<content>.*?)\[/a\]', r'<a href="\g<href>">\g<content></a>'],
        [r'\[img\](?P<content>.*?)\[/img\]', r'<img class="post_image" src="\g<content>" alt="Image"/>'],
        [
            r'\[video\](?P<content>.*?)\[/video\]',
            (r'<video width="560" height="420" controls>'
             '<source src="\g<content>" type=video/webm>'
             '<source src="\g<content>" type=video/ogg>'
             '<source src="\g<content>" type=video/mp4>'
             'Your browser does not support the video tag.'
             '</video>')
        ],
        [r'\[size=(?P<size>.*?)\](?P<content>.*?)\[/size\]', size_repl],
        [r'\[color=(?P<color>.*?)\](?P<content>.*?)\[/color\]', color_repl],
        [r'\[q\](?P<content>.*?)\[/q\]', r'<blockquote>\g<content></blockquote>'],
        [r'\[spoiler\](?P<content>.*?)\[/spoiler\]',
         r'<div class="spoiler"><button>spoiler</button><p>\g<content></p></div>'],
    ]


@register.filter(needs_autoescape=True)
def replace_markdown(value, delete=False, autoescape=True):
    if autoescape:
        value = html.conditional_escape(value)
    if '[' in value and ']' in value:
        for pattern, repl in reg_list:
            if delete:
                repl = r'\g<content>'
            pattern = re.compile(pattern, (re.DOTALL | re.IGNORECASE))
            value = pattern.sub(repl, value)
    return mark_safe(value)

@register.simple_tag
def test_tag():
    return {'hey': 'gril', 'psh': 'pshhhh'}

@register.simple_tag
def get_subforum_info(subforum):
    threads = subforum.thread_set
    threads_num = threads.count()
    posts_num = threads.aggregate(Count('post'))
    posts_num = posts_num['post__count']
    try:
        last_thread = threads.all()[0]
    except IndexError:
        last_thread = None
        last_post = None
    if last_thread:
        try:
            last_post = last_thread.post_set.order_by('-pub_date')[0]
        except IndexError:
            last_post = last_thread
    return {
        'threads_num': threads_num, 'posts_num': posts_num,
        'last_thread': last_thread, 'last_post': last_post
    }

@register.simple_tag
def get_thread_info(thread):
    num_posts = thread.post_set.count()
    range_val = math.ceil(num_posts / settings.POSTS_ON_PAGE) if num_posts > 0 else 1
    thread_pages = list(range(1, range_val + 1))
    thread_pages = thread_pages[:3]
    last_page = range_val
    thread_pages = thread_pages
    posts_num = num_posts
    try:
        last_post = thread.post_set.latest('pub_date')
    except ObjectDoesNotExist:
        last_post = thread
    return {
        'last_page': last_page, 'thread_pages': thread_pages,
        'posts_num': posts_num, 'last_post': last_post
    }


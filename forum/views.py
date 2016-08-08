from django.shortcuts import render, get_object_or_404, resolve_url
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404, HttpResponse
from .models import Category, SubForum, Thread, Post, UserProfile, UserKey
from . import functions
from . import forms
from django.contrib.auth import get_user_model, decorators, login as auth_login, authenticate
import math
from django.contrib.auth import views as auth_views
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.views.generic.list import ListView
from django.conf import settings
from django.utils import html
from django.utils.translation import ugettext_lazy as _
import re
from django.db.models import Q
from itertools import chain
import math
from operator import attrgetter
# def main_page(request, cat=None, template='forum/main_page.html'):
#     if cat is None:
#         cat = Category.objects.order_by('precedence')
#     sub = SubForum.objects.annotate(thread_count=Count('thread', distinct=True),
#                                     post_count=Count('thread__post', distinct=True))
#     sub = list(sub)
#     for s in sub:
#         s.post_count -= s.thread_count  # ocherednoy kostil'\ add custom manager or smth
#         try:
#             s.last_thread = s.thread_set.all()[0]
#         except IndexError:
#             s.last_thread = None
#             s.last_post = None
#             continue
#         s.last_post = s.last_thread.post_set.order_by('-pub_date')[0]
#     context = {
#       'cat': cat, 'sub': sub,
#     }
#     return render(request, template, context)


class ForumView(ListView):
    template_name = 'forum/main_page.html'
    model = Category
    ordering = 'precedence'
    context_object_name = 'cat'

    def get_context_data(self, **kwargs):
        context = super(ForumView, self).get_context_data(**kwargs)
        sub = SubForum.objects.all().add_atts()
        context['sub'] = sub
        return context


class CategoryView(ListView):
    template_name = 'forum/category.html'
    # queryset = SubForum.objects.all().add_atts()
    context_object_name = 'sub'

    def get_queryset(self):
        queryset = SubForum.objects.all().add_atts()
        return queryset

    def get_context_data(self, **kwargs):
        context = super(CategoryView, self).get_context_data(**kwargs)
        cat = get_object_or_404(Category, id=self.kwargs['category_id'])
        context['cat'] = [cat]
        return context


# def category(request, category_id):
#     cat = get_object_or_404(Category, id=category_id)
#     cat = [cat]
#     return main_page(request, cat=cat, template='forum/category.html')


def sub_forum(request, sub_id):
    num_page = request.GET.get('page')
    sub = get_object_or_404(SubForum, id=sub_id)
    threads = sub.thread_set.filter(is_attached=False)
    paginator = Paginator(threads, settings.THREADS_ON_PAGE)
    try:
        page = paginator.page(num_page)
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        page = paginator.page(paginator.num_pages)
    posts_on_page = 10

    def add_atts(arg):
        for t in arg:
            num_posts = t.post_set.count()
            range_val = math.ceil(num_posts / posts_on_page)
            thread_pages = list(range(1, range_val + 1))
            thread_pages = thread_pages[:3]
            t.last_page = range_val
            t.thread_pages = thread_pages
            t.posts_num = num_posts - 1
            t.last_post = t.post_set.order_by('-pub_date')[0]
    attach_threads = None
    if page.number == 1:
        attach_threads = sub.thread_set.filter(is_attached=True).order_by('-pub_date')
        add_atts(attach_threads)
    add_atts(page.object_list)
    init_list = list(paginator.page_range)
    p_index = page.number - 1
    i = p_index - 2 if p_index > 2 else 0
    pages_list = init_list[i:p_index+3]
    context = {
         'sub': sub, 'attach_threads': attach_threads, 'threads': page.object_list, 'page': page,
         'num_page': page.number, 'last_page': paginator.num_pages, 'pages_list': pages_list,
    }
    return render(request, 'forum/sub_forum.html', context)


def thread(request, thread_id):
    form = forms.Post(auto_id=True)
    thread = get_object_or_404(Thread, id=thread_id)
    if request.method == 'POST':
        user = request.user
        if not user.is_authenticated():
            return HttpResponseRedirect(reverse(settings.LOGIN_URL))
        if not user.is_active:
            return HttpResponseRedirect(reverse('forum:activation_required'))
        form = forms.Post(request.POST)
        if form.is_valid():
            full_text = form.cleaned_data['full_text']
            # full_text = html.escape(full_text)
            # full_text = functions.replace_tags(full_text)
            post = Post(user=user, full_text=full_text, thread=thread)
            post.save()
            return HttpResponseRedirect(post.get_absolute_url())
    num_page = request.GET.get('page')
    posts = thread.post_set.order_by('pub_date')
    paginator = Paginator(posts, settings.POSTS_ON_PAGE)
    post_id = request.GET.get('postid')
    if post_id:
        try:
            post = Post.objects.get(id=post_id)
        except ObjectDoesNotExist:
            num_page = 1
        else:
            for p in paginator.page_range:
                if post in paginator.page(p).object_list:
                    num_page = p
                    break
    try:
        page = paginator.page(num_page)
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        page = paginator.page(paginator.num_pages)
    init_list = list(paginator.page_range)
    p_index = page.number - 1
    i = p_index - 2 if p_index > 2 else 0
    pages_list = init_list[i:p_index + 3]
    for p in page.object_list:
        p.full_text = functions.format_in_view(p.full_text)
        signature = p.user.userprofile.signature
        if signature:
            p.signature = functions.format_in_view(signature)

    context = {
        'thread': thread, 'posts': page.object_list, 'pages_list': pages_list,
        'num_page': page.number, 'form': form, 'last_page': paginator.num_pages,
    }
    return render(request, 'forum/thread.html', context)


@decorators.user_passes_test(functions.is_auth, login_url='forum:profile', redirect_field_name=None)
def sign_up(request, redirect_field_name='next'):
    redirect_to = request.POST.get(redirect_field_name,
                                   (request.GET.get(redirect_field_name, '')))
    form = forms.Registration(auto_id=True)
    if request.method == 'POST':
        form = forms.Registration(request.POST, auto_id=True)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            cd = form.cleaned_data
            UserProfile.objects.create(user=user)
            functions.send_confirmation(request, user)
            user = authenticate(username=cd['username'], password=cd['password2'])
            auth_login(request, user)
            return HttpResponseRedirect(reverse('forum:registration_success'))
    context = {'form': form, 'redirect_to': redirect_to}
    return render(request, 'forum/sign_up.html', context)


@decorators.login_required
@decorators.user_passes_test(functions.not_active, login_url=settings.LOGIN_REDIRECT_URL, redirect_field_name=None)
def registration_success(request, redirect_to=settings.LOGIN_REDIRECT_URL):
    # have to replace this with ajax:
    if request.method == 'POST':
        functions.send_confirmation(request, request.user)
        return HttpResponseRedirect(reverse('forum:registration_success'))
    redirect_to = resolve_url(redirect_to)
    return render(request, 'forum/registration_success.html', {'redirect_to': redirect_to})


# doesn't need decorators because it raises 404 at invalid urls
def email_confirmation(request, user_id, key, redirect_to=settings.LOGIN_REDIRECT_URL):
    user = get_object_or_404(get_user_model(), id=user_id)
    user_key = get_object_or_404(UserKey, user=user)
    if user_key.key == key:
        redirect_to = resolve_url(redirect_to)
        if not user.is_active:
            user.is_active = True
        if user_key.email:
            user.email = user_key.email
        user_key.delete()
        user.save()
        return render(request, 'forum/email_confirmed.html', {'redirect_to': redirect_to, 'user': user})
    else:
        raise Http404()


# have to do this with ajax:
@decorators.login_required
@decorators.user_passes_test(functions.not_active, login_url=settings.LOGIN_REDIRECT_URL, redirect_field_name=None)
def activation_required(request):
    if request.method == 'POST':
        functions.send_confirmation(request, request.user)
        return HttpResponseRedirect(reverse('forum:activation_required'))
    return render(request, 'forum/activation_required.html')


@decorators.login_required
@decorators.user_passes_test(functions.active, login_url='forum:activation_required',
                             redirect_field_name=None)
def new_thread(request, sub_id):
    form = forms.NewThread(auto_id=True)
    if request.method == 'POST':
        form = forms.NewThread(request.POST, auto_id=True)
        if form.is_valid():
            thread_title = form.cleaned_data['thread_title']
            full_text = form.cleaned_data['full_text']
            # full_text = html.escape(full_text)
            # full_text = functions.replace_tags(full_text)
            user = request.user
            subforum = SubForum.objects.get(id=sub_id)
            thread = Thread(user=user, thread_title=thread_title,
                            subforum=subforum)
            thread.save()
            post = Post(user=user, full_text=full_text, thread=thread,
                        is_thread=True)
            post.save()
            # return HttpResponseRedirect(reverse('forum:thread', args=(thread.id, 1)))
            return HttpResponseRedirect(thread.get_absolute_url())

    context = {'form': form, 'sub_id': sub_id}
    return render(request, 'forum/new_thread.html', context)


@decorators.user_passes_test(functions.is_auth, login_url='forum:profile', redirect_field_name=None)
def login(request, **kwargs):
    return auth_views.login(request,
                            authentication_form=forms.AuthenticationFormSub,
                            **kwargs)

#
# def post_edit(request, post_id):
#     user = request.user
#     if user.has_perm('forum.change_post_instance'):
#         return render(request, 'forum/change_post.html')
#     else:
#         return HttpResponseRedirect(reverse('forum:main_page'))


@decorators.login_required
def changeprofile(request):
    user = request.user
    user_profile = user.userprofile
    return render(request, 'forum/profile/change_profile.html', {
        'user': user, 'user_profile': user_profile
    })


@decorators.login_required
def profile(request, user_id=None):
    email_confirm = None
    if user_id is None:
        user = request.user
        if not user.is_active:
            email_confirm = True
    else:
        user = get_object_or_404(get_user_model(), id=user_id)
    # have to replace this with ajax:
    if request.method == 'POST':
        if user.is_active:
            raise Http404
        functions.send_confirmation(request, user)
        return HttpResponseRedirect(reverse('forum:profile'))
    user_profile = user.userprofile
    last_posts = user.post_set.order_by('-pub_date')[:10]
    last_threads = user.thread_set.all()[:10]
    post_count = user.post_set.count()
    thread_count = user.thread_set.count()
    post_count -= thread_count
    signature = functions.format_in_view(user_profile.signature)
    context = {
        'user': user, 'user_profile': user_profile, 'last_posts': last_posts,
        'last_threads': last_threads, 'post_count': post_count,
        'thread_count': thread_count, 'email_confirm': email_confirm,
        'signature': signature,
    }
    return render(request, 'forum/profile/profile.html', context)


@decorators.login_required
@decorators.user_passes_test(functions.active, login_url='forum:activation_required',
                             redirect_field_name=None)
def change_avatar(request):
    form = forms.File()
    user = request.user
    user_profile = user.userprofile
    if request.method == 'POST':
        form = forms.File(request.POST, request.FILES)
        if form.is_valid():  # HAVE TO LIMIT UPLOADED FILE SIZE (in template) ETC
            upfile = request.FILES['upload_file']
            avatar_field = user_profile.avatar
            size = (200, 200)
            try:
                functions.handle_avatar(upfile, avatar_field, size)
                return HttpResponseRedirect(reverse('forum:change_avatar'))
            except IOError:
                form.add_error('upload_file', ValidationError(_('File type is not supported')
                                                              , code='not_supported'))
    return render(request, 'forum/profile/change_avatar.html', {
        'form': form, 'user': user, 'user_profile': user_profile,
    })


@decorators.login_required
@decorators.user_passes_test(functions.active, login_url='forum:activation_required',
                             redirect_field_name=None)
def change_info(request):
    user = request.user
    user_profile = user.userprofile
    bound = {
        'first_name': user.first_name, 'last_name': user.last_name,
        'signature': user_profile.signature
    }
    form = forms.Info(bound)
    if request.method == 'POST':
        form = forms.Info(request.POST)
        if form.is_valid():
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.save()
            signature = form.cleaned_data['signature']
            # signature = html.escape(signature)
            # signature = functions.replace_tags(signature)
            user_profile.signature = signature
            user_profile.save()
            return HttpResponseRedirect(reverse('forum:profile'))
    context = {'user': user, 'user_profile': user_profile, 'form': form}
    return render(request, 'forum/profile/change_info.html', context)


@decorators.login_required
def change_email(request):
    user = request.user
    sent = False
    if request.method == 'POST':
        form = forms.Email(request.POST)
        if form.is_valid():
            try:
                userkey = UserKey.objects.get(user=user)
                userkey.email = form.cleaned_data['new_email']
            except ObjectDoesNotExist:
                userkey = UserKey(user=user, email=form.cleaned_data['new_email'])
            #user.userkey.email = form.cleaned_data['new_email']
            userkey.save()
            functions.send_confirmation(request, user, userkey.email,
                                        functions.email_change_msg)
            #return HttpResponseRedirect(reverse('forum:change_profile'))
            sent = True
    else:
        form = forms.Email()
    context = {'user': user, 'form': form, 'sent': sent}
    return render(request, 'forum/profile/change_email.html', context)


def search(request):
    form = forms.Search()
    if request.method == 'GET' and request.GET:
        form = forms.Search(request.GET)
        if form.is_valid():
            words = form.cleaned_data.get('search')
            user = form.cleaned_data.get('user')
            subforums = form.cleaned_data.get('subforums')
            search_by = form.cleaned_data.get('search_by')
            sort_by = form.cleaned_data.get('sort_by')
            num_page = request.GET.get('page')
            get = request.GET.copy()
            if num_page:
                del get['page']
            get = get.urlencode()
            words = re.split(r'\W+', words)
            query = Post.objects.all()
            if user:
                query = Post.objects.filter(user__username=user)
            if subforums:
                query = query.filter(thread__subforum__in=subforums)
            thread_query = Q(thread__thread_title__icontains=words[0])
            for i in words[1:]:
                thread_query = thread_query & Q(thread__thread_title__icontains=i)
            post_query = Q(full_text__icontains=words[0])
            for i in words[1:]:
                post_query = post_query & Q(full_text__icontains=i)
            t_query = query.filter(is_thread=True)
            t_query = t_query.filter(thread_query | post_query)
            if search_by == 't':
                query = t_query
            else:
                query = query.filter(is_thread=False)
                query = query.filter(post_query)
                if search_by == 'pt':
                    query = chain(query, t_query)
            order_dict = {'p': 'pub_date', 'rt': 'rating'}
            query = sorted(query, key=attrgetter(order_dict[sort_by]), reverse=True)
            paginator = Paginator(query, settings.POSTS_ON_PAGE)
            try:
                page = paginator.page(num_page)
            except PageNotAnInteger:
                page = paginator.page(1)
            except EmptyPage:
                page = paginator.page(paginator.num_pages)
            init_list = list(paginator.page_range)
            p_index = page.number - 1
            i = p_index - 2 if p_index > 2 else 0
            pages_list = init_list[i:p_index + 3]

            # escape user formatting
            for post in page:
                post.full_text = functions.replace_tags(post.full_text, delete=True)
            num_res = len(query)
            return render(request, 'forum/search_form.html', {
                'query': page, 'pages_list': pages_list, 'form': form,
                'last_page': paginator.num_pages, 'get': get,
                'num_page': page.number, 'num_res': num_res,
            })
    context = {'form': form,}
    return render(request, 'forum/search_form.html', context)


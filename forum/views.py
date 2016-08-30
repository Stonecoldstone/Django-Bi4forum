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
from django.views.generic.edit import UpdateView
from django.conf import settings
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
import re
from django.db.models import Q, F
from itertools import chain
from operator import attrgetter
from django.utils import timezone


def rating(request, obj, obj_id):
    obj_dict = {'thread': Thread, 'post': Post}
    user = request.user
    if request.method == 'POST':
        like = request.POST.get('like')
        dislike = request.POST.get('dislike')
        model = obj_dict[obj]
        obj = get_object_or_404(model, id=obj_id)
        result = 0
        if like:
            relate = obj.users_liked
            digit = 1
        elif dislike:
            relate = obj.users_disliked
            digit = -1
        else:
            return HttpResponseRedirect(obj.get_absolute_url())
        try:
            relate.get(id=user.id)
        except ObjectDoesNotExist:
            relate.add(user)
            result += digit
        else:
            relate.remove(user)
            result -= digit
        model.objects.filter(id=obj_id).update(rating=F('rating') + result)
        return HttpResponseRedirect(obj.get_absolute_url())
    else:
        raise Http404

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
        queryset = SubForum.objects.filter(category__id=self.kwargs['category_id'])\
            .add_atts()
        return queryset

    def get_context_data(self, **kwargs):
        context = super(CategoryView, self).get_context_data(**kwargs)
        cat = get_object_or_404(Category, id=self.kwargs['category_id'])
        context['cat'] = [cat]
        return context


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

    def add_atts(arg):
        for t in arg:
            num_posts = t.post_set.count()
            range_val = math.ceil(num_posts / settings.POSTS_ON_PAGE) if num_posts > 0 else 1
            thread_pages = list(range(1, range_val + 1))
            thread_pages = thread_pages[:3]
            t.last_page = range_val
            t.thread_pages = thread_pages
            t.posts_num = num_posts
            try:
                t.last_post = t.post_set.latest('pub_date')
            except ObjectDoesNotExist:
                t.last_post = t
    attach_threads = None
    if page.number == 1:
        attach_threads = sub.thread_set.filter(is_attached=True).order_by('-pub_date')
        attach_threads = attach_threads.select_related('user__userprofile')
        add_atts(attach_threads)
    page.object_list = page.object_list.select_related('user__userprofile')
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
    thrd = get_object_or_404(Thread, id=thread_id)
    if request.method == 'POST':
        user = request.user
        if not user.is_authenticated():
            return HttpResponseRedirect(reverse(settings.LOGIN_URL))
        if not user.is_active:
            return HttpResponseRedirect(reverse('forum:activation_required'))
        form = forms.Post(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = user
            post.thread = thrd
            post.save()
            return HttpResponseRedirect(post.get_absolute_url())
    num_page = request.GET.get('page')
    posts = thrd.post_set.order_by('pub_date')
    posts = list(posts)
    posts.insert(0, thrd)
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
        # p.is_liked = p.is_liked(user)
        # p.is_disliked = p.is_disliked(user)

    context = {
        'thread': thrd, 'posts': page.object_list, 'pages_list': pages_list,
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
            user = request.user
            subforum = get_object_or_404(SubForum, id=sub_id)
            thread = form.save(commit=False)
            thread.user = user
            thread.subforum = subforum
            # thread.raw_text = functions.replace_tags(thread.full_text, delete=True)
            thread.save()
            return HttpResponseRedirect(thread.get_absolute_url())

    context = {'form': form, 'sub_id': sub_id}
    return render(request, 'forum/new_thread.html', context)


@decorators.user_passes_test(functions.is_auth, login_url='forum:profile', redirect_field_name=None)
def login(request, **kwargs):
    return auth_views.login(request,
                            authentication_form=forms.AuthenticationFormSub,
                            **kwargs)


class EditThread(UpdateView):
    model = Thread
    form_class = forms.NewThreadEdit
    template_name = 'forum/edit_thread.html'

    @method_decorator(decorators.login_required)
    @method_decorator(decorators.user_passes_test(functions.active,
                                                  login_url='forum:activation_required',
                                                  redirect_field_name=None))
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if self.request.user.id != obj.user.id:
            raise Http404
        return super(EditThread, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.edit_date = timezone.now()
        return super(EditThread, self).form_valid(form)

class EditPost(UpdateView):
    model = Post
    form_class = forms.Post
    template_name = 'forum/edit_post.html'

    @method_decorator(decorators.login_required)
    @method_decorator(decorators.user_passes_test(functions.active,
                                                  login_url='forum:activation_required',
                                                  redirect_field_name=None))
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if self.request.user.id != obj.user.id:
            raise Http404
        return super(EditPost, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.edit_date = timezone.now()
        return super(EditPost, self).form_valid(form)


# class Edit(UpdateView):
#     template_name = 'forum/edit.html'
#     args_dict = {'thread': (forms.NewThreadEdit, Thread), 'post': (forms.Post, Post)}
#
#     def dispatch(self, request, *args, **kwargs):
#         kinds = ['thread', 'post']
#         if self.kwargs['kind'] not in kinds:
#             raise Http404
#         obj = self.get_object()
#         if self.request.user.id != obj.user.id:
#             raise Http404
#         return super(Edit, self).dispatch(request, *args, **kwargs)
#
#     def get_form_class(self):
#         arg = self.kwargs['kind']
#         # if arg == 'thread':
#         #     return forms.NewThreadEdit
#         # else:
#         #     return forms.Post
#         return self.args_dict[arg][0]
#
#     def get_object(self):
#         model = self.args_dict[self.kwargs['kind']][1]
#         pk = self.kwargs['pk']
#         obj = get_object_or_404(model, id=pk)
#         return obj



def password_change(request):
    context = {'user_profile': request.user.userprofile}
    return auth_views.password_change(request,
                                      template_name='forum/profile/change_password.html',
                                      post_change_redirect='forum:password_changed',
                                      password_change_form=forms.PasswordChange,
                                      current_app=None, extra_context=context)


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
    try:
        user_profile = user.userprofile
    except ObjectDoesNotExist:
        user_profile = UserProfile(user=user)
        user_profile.save()
    last_posts = user.post_set.order_by('-pub_date')[:10]\
        .select_related('thread')
    last_threads = user.thread_set.all()[:10]
    post_count = user.post_set.count()
    thread_count = user.thread_set.count()
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
            # avatar_field = user_profile.avatar
            # size = (200, 200)
            try:
                user_profile.avatar = upfile
                user_profile.save()
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
            userkey.save()
            functions.send_confirmation(request, user, userkey.email,
                                        functions.email_change_msg)
            sent = True
    else:
        form = forms.Email()
    context = {'user': user, 'user_profile': user.userprofile, 'form': form, 'sent': sent}
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
            titles_query = Thread.objects.all()
            if user:
                titles_query = Thread.objects.filter(user__username=user)
            if subforums:
                titles_query = titles_query.filter(subforum__in=subforums)
            title_words = Q(thread_title__icontains=words[0])
            for i in words[1:]:
                title_words = title_words & Q(thread_title__icontains=i)
            titles_query = titles_query.filter(title_words)
            if search_by == 't':
                query = titles_query
            else:
                post_query = Post.objects.all()
                thread_query = Thread.objects.all()
                if user:
                    post_query = Post.objects.filter(user__username=user)
                    thread_query = Thread.objects.filter(user__username=user)
                if subforums:
                    post_query = post_query.filter(thread__subforum__in=subforums)
                    thread_query = thread_query.filter(subforum__in=subforums)
                text_query = Q(raw_text__icontains=words[0])
                for i in words[1:]:
                    text_query = text_query & Q(raw_text__icontains=i)
                post_query = post_query.filter(text_query)
                thread_query = thread_query.filter(text_query)
                if search_by == 'p':
                    query = post_query
                else:
                    query = set(chain(titles_query, post_query, thread_query))
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
            num_res = len(query)
            return render(request, 'forum/search_form.html', {
                'query': page, 'pages_list': pages_list, 'form': form,
                'last_page': paginator.num_pages, 'get': get,
                'num_page': page.number, 'num_res': num_res,
            })
    context = {'form': form}
    return render(request, 'forum/search_form.html', context)


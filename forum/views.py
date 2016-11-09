from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import (authenticate, decorators, get_user_model,
                                 update_session_auth_hash)
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.core.urlresolvers import reverse
from django.http import (Http404, HttpResponse, HttpResponseRedirect,
                         JsonResponse)
from django.shortcuts import get_object_or_404, render, resolve_url
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.http import is_safe_url
from django.utils.translation import ugettext_lazy as _
from django.views.decorators import cache, csrf, debug
from django.views.decorators.http import require_POST
from django.views.generic.edit import FormView, UpdateView
from django.views.generic.list import ListView
from haystack.query import SearchQuerySet

from . import settings as forum_settings
from . import forms, functions
from .models import Category, Post, SubForum, Thread


@decorators.login_required
@require_POST
def rating(request):
    obj_dict = {'thread': Thread, 'post': Post}
    user = request.user
    action = request.POST.get('action')
    obj_id = request.POST.get('id')
    obj = request.POST.get('object')
    try:
        model = obj_dict[obj]
        obj = model.objects.get(id=obj_id)
        if action == 'like':
            query_set = obj.users_liked
        elif action == 'dislike':
            query_set = obj.users_disliked
    except(KeyError, NameError, ObjectDoesNotExist):
        return JsonResponse({'status': 'not okay'})
    try:
        query_set.get(id=user.id)
    except ObjectDoesNotExist:
        query_set.add(user)
    else:
        query_set.remove(user)
    return JsonResponse({'status': 'ok', 'count': obj.get_rating()})


class ForumView(ListView):
    template_name = 'forum/main_page.html'
    model = Category
    ordering = 'precedence'
    context_object_name = 'cat'

    def get_context_data(self, **kwargs):
        context = super(ForumView, self).get_context_data(**kwargs)
        sub = SubForum.objects.all()
        context['sub'] = sub
        return context


class CategoryView(ListView):
    template_name = 'forum/category.html'
    # queryset = SubForum.objects.all().add_atts()
    context_object_name = 'sub'

    def get_queryset(self):
        queryset = SubForum.objects.filter(category__id=self.kwargs['category_id'])
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
    paginator = Paginator(threads, forum_settings.THREADS_ON_PAGE)
    try:
        page = paginator.page(num_page)
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        page = paginator.page(paginator.num_pages)
    attach_threads = None
    if page.number == 1:
        attach_threads = sub.thread_set.filter(is_attached=True).order_by('-pub_date')
        attach_threads = attach_threads.select_related('user__userprofile')
    page.object_list = page.object_list.select_related('user__userprofile')
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
    user = request.user
    if request.method == 'POST':
        if not user.is_authenticated():
            return HttpResponseRedirect(reverse(forum_settings.LOGIN_URL))
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
    paginator = Paginator(posts, forum_settings.POSTS_ON_PAGE)
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
            user = authenticate(username=cd['username'], password=cd['password2'])
            auth_login(request, user)
            functions.send_confirmation(request, user, user.email,
                                        subject_template='forum/registration/email_subject.html',
                                        message_template='forum/registration/email_body.html')
            return HttpResponseRedirect(reverse('forum:registration_success'))
    context = {'form': form, 'redirect_to': redirect_to}
    return render(request, 'forum/registration/sign_up.html', context)


@decorators.login_required
@decorators.user_passes_test(functions.not_active, login_url=forum_settings.LOGIN_REDIRECT_URL, redirect_field_name=None)
def registration_success(request, redirect_to=forum_settings.LOGIN_REDIRECT_URL):
    # have to replace this with ajax:
    if request.method == 'POST':
        email = request.user.email
        functions.send_confirmation(request, request.user, email,
                                    subject_template='forum/registration/email_subject.html',
                                    message_template='forum/registration/email_body.html')
        messages_text = 'Confirmation mail has been sent to {}'.format(email)
        messages.success(request, messages_text)
        return HttpResponseRedirect(reverse('forum:registration_success'))
    redirect_to = resolve_url(redirect_to)
    return render(request, 'forum/registration/registration_success.html', {'redirect_to': redirect_to})


# doesn't need decorators because it raises 404 at invalid urls
def email_confirmation(request, user_id, token, redirect_to=forum_settings.LOGIN_REDIRECT_URL):
    user = get_object_or_404(get_user_model(), id=user_id)
    if functions.EmailTokenGenerator().check_token(user, token):
        redirect_to = resolve_url(redirect_to)
        if not user.is_active:
            user.is_active = True
            user.save()
        user.userprofile.substitute_mail()
        return render(request, 'forum/registration/email_confirmed.html', {'redirect_to': redirect_to, 'user': user})
    else:
        raise Http404()


@decorators.login_required
@decorators.user_passes_test(functions.not_active, login_url=forum_settings.LOGIN_REDIRECT_URL, redirect_field_name=None)
def activation_required(request):
    if request.method == 'POST':
        email = request.user.email
        functions.send_confirmation(request, request.user, email,
                                    subject_template='forum/registration/email_subject.html',
                                    message_template='forum/registration/email_body.html')
        messages_text = 'Confirmation mail has been sent to {}'.format(email)
        messages.success(request, messages_text)
        return HttpResponseRedirect(reverse('forum:activation_required'))
    return render(request, 'forum/registration/activation_required.html')


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
            thread.save()
            return HttpResponseRedirect(thread.get_absolute_url())

    context = {'form': form, 'sub_id': sub_id}
    return render(request, 'forum/new_thread.html', context)


# @decorators.user_passes_test(functions.is_auth, login_url='forum:profile', redirect_field_name=None)
# def login(request, **kwargs):
#     return auth_views.login(request,
#                             authentication_form=forms.AuthenticationFormSub,
#                             **kwargs)


class Login(FormView):
    template_name = 'forum/registration/login.html'
    form_class = forms.AuthenticationFormSub

    @method_decorator(decorators.user_passes_test(functions.is_auth,
                                                  login_url='forum:profile',
                                                  redirect_field_name=None))
    @method_decorator(debug.sensitive_post_parameters('password'))
    @method_decorator(csrf.csrf_protect)
    @method_decorator(cache.never_cache)
    def dispatch(self, request, *args, **kwargs):
        return super(Login, self).dispatch(request, *args, **kwargs)

    def get_success_url(self):
        redirect_to = self.request.POST.get('next',
                                       self.request.GET.get('next', ''))
        if not is_safe_url(url=redirect_to, host=self.request.get_host()):
            redirect_to = reverse(forum_settings.LOGIN_REDIRECT_URL)
        return redirect_to

    def get(self, request, *args, **kwargs):
        if request.is_ajax():
            form = self.get_form().as_ul()
            return HttpResponse(form)
        else:
            return super(Login, self).get(request, *args, **kwargs)

    def form_valid(self, form):
        auth_login(self.request, form.get_user())
        return super(Login, self).form_valid(form)


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

class EditPost(EditThread):
    model = Post
    form_class = forms.Post
    template_name = 'forum/edit_post.html'

    # @method_decorator(decorators.login_required)
    # @method_decorator(decorators.user_passes_test(functions.active,
    #                                               login_url='forum:activation_required',
    #                                               redirect_field_name=None))
    # def dispatch(self, request, *args, **kwargs):
    #     obj = self.get_object()
    #     if self.request.user.id != obj.user.id:
    #         raise Http404
    #     return super(EditPost, self).dispatch(request, *args, **kwargs)
    #
    # def form_valid(self, form):
    #     form.instance.edit_date = timezone.now()
    #     return super(EditPost, self).form_valid(form)


@decorators.login_required
@decorators.user_passes_test(functions.active, login_url='forum:activation_required',
                             redirect_field_name=None)
@debug.sensitive_post_parameters()
def password_change(request):
    user = request.user
    if request.method == "POST":
        form = forms.PasswordChange(user=user, data=request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            messages.success(request, 'Your password was changed.')
            return HttpResponseRedirect(reverse('forum:change_password'))
    else:
        form = forms.PasswordChange(user=user)
    return render(request, 'forum/profile/change_password.html',
                  {'form': form, 'user': user, 'user_profile': user.userprofile})


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
        functions.send_confirmation(request, user, user.email,
                                    subject_template='forum/registration/email_subject.html',
                                    message_template='forum/registration/email_body.html')
        messages.success(request, 'Mail has been sent to {}'.format(user.email))
        return HttpResponseRedirect(reverse('forum:profile'))
    user_profile = user.userprofile
    last_posts = user.post_set.order_by('-pub_date')[:10]\
        .select_related('thread')
    last_threads = user.thread_set.all()[:10]
    post_count = user.post_set.count()
    thread_count = user.thread_set.count()
    context = {
        'user': user, 'user_profile': user_profile, 'last_posts': last_posts,
        'last_threads': last_threads, 'post_count': post_count,
        'thread_count': thread_count, 'email_confirm': email_confirm,
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
        if form.is_valid():
            upfile = request.FILES['upload_file']
            try:
                user_profile.avatar = upfile
                user_profile.save()
                messages.success(request, 'Your avatar was changed.')
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
            user_profile.signature = signature
            user_profile.save()
            messages.success(request, 'Your profile information was changed.')
            return HttpResponseRedirect(reverse('forum:change_info'))
    context = {'user': user, 'user_profile': user_profile, 'form': form}
    return render(request, 'forum/profile/change_info.html', context)


@decorators.login_required
def change_email(request):
    user = request.user
    sent = False
    if request.method == 'POST':
        form = forms.Email(request.POST)
        if form.is_valid():
            new_email = form.cleaned_data['new_email']
            user.userprofile.new_email = new_email
            user.userprofile.save()
            subject = 'forum/registration/email_subject.html'
            message = 'forum/profile/change_email_message.html'
            functions.send_confirmation(request, user, new_email,
                                        subject_template=subject,
                                        message_template=message)
            messages_text = 'Confirmation mail has been sent to {}'.format(new_email)
            messages.success(request, messages_text)
    else:
        form = forms.Email()
    context = {'user': user, 'user_profile': user.userprofile, 'form': form, 'sent': sent}
    return render(request, 'forum/profile/change_email.html', context)


def search(request):
    form = forms.Search()
    if 'search' in request.GET or 'user' in request.GET:
        form = forms.Search(request.GET)
        if form.is_valid():
            words = form.cleaned_data.get('search')
            user = form.cleaned_data.get('user')
            subforums = form.cleaned_data.get('subforums')
            only_threads = form.cleaned_data.get('only_threads')
            sort_by = form.cleaned_data.get('sort_by')
            num_page = request.GET.get('page')
            get = request.GET.copy()
            if num_page:
                del get['page']
            get = get.urlencode()
            if only_threads:
                query = SearchQuerySet().models(Thread)
            else:
                query = SearchQuerySet()
            if words:
                query = query.filter(content=words)
            if user:
                query = query.filter(author=user)
            if subforums:
                query = query.filter(subforum__in=subforums)
            order_dict = {'p': '-pub_date', 'rt': '-rating'}
            sort_by = order_dict.get(sort_by)
            if sort_by:
                query = query.order_by(sort_by)
            query = query.load_all()
            paginator = Paginator(query, forum_settings.POSTS_ON_PAGE)
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
            context = {
                'query': page, 'pages_list': pages_list, 'form': form,
                'last_page': paginator.num_pages, 'get': get,
                'num_page': page.number, 'num_res': num_res,
            }
            return render(request, 'forum/search_form.html', context)
    return render(request, 'forum/search_form.html', {'form': form})

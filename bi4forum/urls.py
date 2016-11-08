from django.conf.urls import url
from . import views
from django.contrib.auth import views as auth_views

app_name = 'forum'
urlpatterns = [
    # url(r'^$', views.main_page, name='main_page'),
    url(r'^$', views.ForumView.as_view(), name='main_page'),
    url(r'^(?P<category_id>\d+)/category/$', views.CategoryView.as_view(), name='category'),
    url(r'^(?P<sub_id>\d+)/sub_forum/$',
        views.sub_forum, name='sub_forum'),
    url(r'^(?P<thread_id>\d+)/thread/$', views.thread, name='thread'),
    url(r'^sign_up/$', views.sign_up, name='sign_up'),
    url(r'^registration_success/$', views.registration_success, name='registration_success'),
    url(
        r'^email_confirmation/(?P<user_id>\d+)/(?P<token>[-\w]+)/$',
        views.email_confirmation, name='email_confirmation'
    ),
    url(r'^activation_required/$', views.activation_required, name='activation_required'),
    # url(r'^login/$', views.login, {'template_name': 'forum/login.html'}, name='login'),
    url(r'^login/$', views.Login.as_view(), name='login'),
    url(r'^logout/$', auth_views.logout, {'next_page': 'forum:main_page'}, name='logout'),
    url(r'^(?P<sub_id>\d+)/new_thread/$', views.new_thread, name='new_thread'),
    url(r'^profile/$', views.profile, name='profile'),
    url(r'^profile/(?P<user_id>\d+)/$', views.profile, name='profile'),
    url(r'^change_profile/$', views.changeprofile, name='change_profile'),
    url(r'^change_avatar/$', views.change_avatar, name='change_avatar'),
    url(r'^change_info/$', views.change_info, name='change_info'),
    url(r'^change_email/$', views.change_email, name='change_email'),
    url(r'^change_password/$', views.password_change, name='change_password'),
    url(r'^password_changed/$', auth_views.password_change_done,
        {
            'template_name': 'forum/profile/password_changed.html',
            'extra_context': {'redirect_to': 'forum:profile'}
        },
        name='password_changed'),
    url(r'^search/$', views.search, name='search'),
    url(r'^(?P<pk>\d+)/edit_thread/$', views.EditThread.as_view(), name='edit_thread'),
    url(r'^(?P<pk>\d+)/edit_post/$', views.EditPost.as_view(), name='edit_post'),
    url(r'^rating/$', views.rating, name='rating'),
]

from django.test import TestCase
from django.contrib.auth.models import User
from forum import models

class TestForumView(TestCase):
    fixtures = ['users.json', 'forum_testdata.json']

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.get(username='henry_miller')
        cls.search = '<a class="button" href="/main_page/search/">Search</a>'
        cls.logout = '<a class="button" href="/main_page/logout/?next=/main_page/">Log out</a>'
        cls.profile = '<a class="button" href="/main_page/profile/">{}</a>'.format(cls.user.username)
        cls.login = '<a class="button" href="/main_page/login/?next=/main_page/">Log in</a>'
        cls.signup = '<a class="button" href="/main_page/sign_up/?next=/main_page/">Sign up</a>'
        cls.logged_in = [cls.search, cls.logout, cls.profile]
        cls.anonymous = [cls.login, cls.signup]

    def test_category_precedence(self):
        response = self.client.get('/main_page/')
        cat = response.context['cat']
        self.assertQuerysetEqual(cat, ['<Category: First>', '<Category: Second>'])

    def test_anonymous_user_sees_login_and_signup(self):
        response = self.client.get('/main_page/')
        for s in self.anonymous:
            self.assertContains(response, s, html=True)
        for s in self.logged_in:
            self.assertNotContains(response, s, html=True)

    def test_logged_in_user_sees_search_logout_and_profile(self):
        self.client.force_login(self.user)
        response = self.client.get('/main_page/')
        for s in self.logged_in:
            self.assertContains(response, s, html=True)
        for s in self.anonymous:
            self.assertNotContains(response, s, html=True)



class TestCategoryView(TestCase):
    fixtures = ['users.json', 'forum_testdata.json']

    def test_category_matches(self):
        response = self.client.get('/main_page/2/category/')
        cat = response.context['cat'][0]
        self.assertEqual(cat.id, 2)

    def test_wrong_id_404(self):
        response = self.client.get('/main_page/4/category/')
        self.assertEqual(response.status_code, 404)

    def test_subforums_right_precedence(self):
        response = self.client.get('/main_page/1/category/')
        sub = response.context['sub']
        self.assertEqual([s.precedence for s in sub], [1, 2])


class TestSubForumView(TestCase):
    fixtures = ['users.json', 'forum_testdata.json']

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.get(username='henry_miller')

    def test_subforum_matches(self):
        response = self.client.get('/main_page/1/sub_forum/?page=1')
        sub = response.context['sub']
        self.assertEqual(sub.id, 1)

    def test_wrong_id_404(self):
        response = self.client.get('/main_page/10/sub_forum/?page=1')
        self.assertEqual(response.status_code, 404)

    def test_new_thread_first(self):
        sub = models.SubForum.objects.get(id=1)
        thread = models.Thread(subforum=sub, user=self.user, thread_title='New')
        thread.save()
        post = models.Post(thread=thread, user=self.user, full_text='New')
        post.save()
        response = self.client.get('/main_page/1/sub_forum/?page=1')
        threads = response.context['threads']
        self.assertEqual(threads[0], thread)



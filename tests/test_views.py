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
        cls.sub = models.SubForum.objects.get(id=1)

    def test_subforum_matches(self):
        response = self.client.get('/main_page/1/sub_forum/?page=1')
        sub = response.context['sub']
        self.assertEqual(sub.id, 1)

    def test_wrong_id_404(self):
        """
        Test that view raises 404 when url with wrong id argument is requsted.
        """
        response = self.client.get('/main_page/10/sub_forum/?page=1')
        self.assertEqual(response.status_code, 404)

    def test_new_thread_first(self):
        thread = models.Thread(subforum=self.sub, user=self.user, thread_title='New', full_text='New')
        thread.save()
        response = self.client.get('/main_page/1/sub_forum/?page=1')
        threads = response.context['threads']
        self.assertEqual(threads[0], thread)

    def test_thread_atts(self):
        """
        Test attributes that is created for every thread instance in a view.
        """
        thread = models.Thread.objects.get(id=640)
        for i in range(25):
            post = models.Post(thread=thread, user=self.user,
                               full_text='{}'.format(i))
            post.save()
        response = self.client.get('/main_page/1/sub_forum/?page=1')
        thread = response.context['threads'][0]
        self.assertEqual(thread.last_page, 2)
        self.assertEqual(thread.thread_pages, [1, 2])
        self.assertEqual(thread.posts_num, 26)

    def test_thread_last_post_att_is_thread(self):
        """
        Test "last_post" attribute that's added to every thread instance.
        If thread contains posts, attribute should point to post that was created last;
        if not - to thread itself.
        """
        # thread = models.Thread.objects.get(id=642)
        response = self.client.get('/main_page/2/sub_forum/?page=1')
        thread = response.context['threads'][0]
        self.assertEqual(thread.last_post, thread)

    def test_thread_last_post_is_post(self):
        thread = models.Thread.objects.get(id=642)
        post = models.Post(thread=thread, full_text='Last post', user=self.user)
        post.save()
        response = self.client.get('/main_page/2/sub_forum/?page=1')
        thread = response.context['threads'][0]
        self.assertEqual(thread.last_post, post)

    def test_attached_threads_on_first_page(self):
        """
        Test that context contains attached threads if first page is requested.
        :return:
        """
        response = self.client.get('/main_page/1/sub_forum/?page=1')
        threads = response.context['attach_threads']
        self.assertTrue(threads)
        self.assertTrue(threads[0].is_attached)

    def test_attached_threads_on_second_page(self):
        """
        Attached threads should be "None" if not first page is requested.
        """
        for i in range(25):
            models.Thread.objects.create(subforum=self.sub, user=self.user,
                                         thread_title='{}'.format(i),
                                         )
        response = self.client.get('/main_page/1/sub_forum/?page=2')
        threads = response.context['attach_threads']
        self.assertIsNone(threads)









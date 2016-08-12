from django.test import TestCase
from django.contrib.auth.models import User
from forum import models
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.conf import settings
from . import data

class TestForumView(TestCase):
    fixtures = ['users.json', 'forum_testdata.json']

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.get(username='Lana')
        cls.search = '<a class="button" href="/main_page/search/">Search</a>'
        cls.logout = '<a class="button" href="/main_page/logout/?next=/main_page/">Log out</a>'
        cls.profile = '<a class="button" href="/main_page/profile/">{}</a>'.format(cls.user.username)
        cls.login = '<a class="button" href="/main_page/login/?next=/main_page/">Log in</a>'
        cls.signup = '<a class="button" href="/main_page/sign_up/?next=/main_page/">Sign up</a>'
        cls.logged_in = [cls.logout, cls.profile]
        cls.anonymous = [cls.login, cls.signup]
        cls.url = reverse('forum:main_page')

    def test_category_precedence(self):
        first = models.Category.objects.get(title='First')
        second = models.Category.objects.get(title='Second')
        precedence_list = [first.precedence, second.precedence]
        self.assertEqual([1, 2], precedence_list)
        response = self.client.get(self.url)
        cat = response.context['cat']
        self.assertQuerysetEqual(cat, ['<Category: First>', '<Category: Second>'])

    def test_anonymous_user_sees_login_and_signup(self):
        response = self.client.get(self.url)
        for s in self.anonymous:
            self.assertContains(response, s, html=True)
        for s in self.logged_in:
            self.assertNotContains(response, s, html=True)
        self.assertContains(response, self.search)

    def test_logged_in_user_sees_search_logout_and_profile(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        for s in self.logged_in:
            self.assertContains(response, s, html=True)
        for s in self.anonymous:
            self.assertNotContains(response, s, html=True)
        self.assertContains(response, self.search)



class TestCategoryView(TestCase):
    fixtures = ['users.json', 'forum_testdata.json']

    def test_category_matches(self):
        response = self.client.get(reverse('forum:category', args=(2,)))
        cat = response.context['cat'][0]
        self.assertEqual(cat.id, 2)

    def test_wrong_id_404(self):
        with self.assertRaises(ObjectDoesNotExist):
            models.Category.objects.get(id=4)
        response = self.client.get(reverse('forum:category', args=(4,)))
        self.assertEqual(response.status_code, 404)

    def test_subforums_right_precedence(self):
        response = self.client.get(reverse('forum:category', args=(1,)))
        sub = response.context['sub']
        self.assertEqual([s.precedence for s in sub], [1, 2])


class TestSubForumView(TestCase):
    fixtures = ['users.json', 'forum_testdata.json']

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.get(username='Lana')
        cls.sub = models.SubForum.objects.get(id=1)
        cls.url_1 = reverse('forum:sub_forum', args=(1,))

    def test_subforum_matches(self):
        response = self.client.get('{}?page=1'.format(self.url_1))
        sub = response.context['sub']
        self.assertEqual(sub.id, 1)

    def test_wrong_id_404(self):
        """
        Test that view raises 404 when url with wrong id argument is requsted.
        """
        with self.assertRaises(ObjectDoesNotExist):
            models.SubForum.objects.get(id=10)
        url = reverse('forum:sub_forum', args=(10,))
        response = self.client.get('{}?page=1'.format(url))
        self.assertEqual(response.status_code, 404)

    def test_new_thread_first(self):
        thread = models.Thread(subforum=self.sub, user=self.user, thread_title='New', full_text='New')
        thread.save()
        response = self.client.get('{}?page=1'.format(self.url_1))
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
        posts_num = thread.post_set.count()
        response = self.client.get('{}?page=1'.format(self.url_1))
        thread = response.context['threads'][0]
        self.assertEqual(thread.last_page, 2)
        self.assertEqual(thread.thread_pages, [1, 2])
        self.assertEqual(thread.posts_num, posts_num)

    def test_thread_last_post_att_is_thread(self):
        """
        Test "last_post" attribute that's added to every thread instance.
        If thread contains posts, attribute should point to post that was created last;
        if not - to thread itself.
        """
        # thread = models.Thread.objects.get(id=642)
        url = reverse('forum:sub_forum', args=(2,))
        response = self.client.get('{}?page=1'.format(url))
        thread = response.context['threads'][0]
        self.assertEqual(thread.last_post, thread)

    def test_thread_last_post_is_post(self):
        thread = models.Thread.objects.get(id=642)
        post = models.Post(thread=thread, full_text='Last post', user=self.user)
        post.save()
        url = reverse('forum:sub_forum', args=(2,))
        response = self.client.get('{}?page=1'.format(url))
        thread = response.context['threads'][0]
        self.assertEqual(thread.last_post, post)

    def test_attached_threads_on_first_page(self):
        """
        Test that context contains attached threads if first page is requested.
        """
        response = self.client.get('{}?page=1'.format(self.url_1))
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
        response = self.client.get('{}?page=2'.format(self.url_1))
        threads = response.context['attach_threads']
        self.assertIsNone(threads)

    def test_user_sees_new_thread(self):
        """
        "New Thread" link should be available to authenticated users.
        """
        link = '<a class="button" href="/main_page/1/new_thread/">New thread</a>'
        url = '{}?page=1'.format(self.url_1)
        response = self.client.get(url)
        self.assertNotContains(response, link, html=True)
        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertContains(response, link, html=True)


class TestThreadView(TestCase):
    fixtures = ['users.json', 'forum_testdata.json']

    def test_returns_200(self):
        response = self.client.get(reverse('forum:thread', args=(640,)))
        self.assertEqual(response.status_code, 200)

    def test_raises_400_when_nonexistent(self):
        with self.assertRaises(ObjectDoesNotExist):
            models.Thread.objects.get(id=1000)
        response = self.client.get(reverse('forum:thread', args=(1000,)))
        self.assertEqual(response.status_code, 404)




class TestThreadViewPost(TestCase):
    fixtures = ['users.json', 'forum_testdata.json']

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.get(username='Lana')
        cls.data = {'full_text': 'Hello!'}
        cls.url = reverse('forum:thread', args=(640,))

    def test_anonymous_redirected(self):
        """
        Ensure anonymous users are redirected to login page.
        """
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse(settings.LOGIN_URL))

    def test_inactive_redirected(self):
        """
        Test that users with "is_active" attribute set to false
         are redirected to activation page.
        """
        user = User.objects.get(username='user_inactive')
        self.assertFalse(user.is_active)
        self.client.force_login(user)
        resp = self.client.post(self.url, self.data)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], reverse('forum:activation_required'))

    def test_bad_post(self):
        # test that url with non-existent thread id raises 404
        self.client.force_login(self.user)
        with self.assertRaises(ObjectDoesNotExist):
            models.Thread.objects.get(id=1000)
        bad_url = reverse('forum:thread', args=(1000,))
        resp = self.client.post(bad_url, self.data)
        self.assertEqual(resp.status_code, 404)
        # send empty request
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['form']['full_text'].errors, ['This field is required.'])
        # send junk data
        resp = self.client.post(self.url, {'blabla': 'Hello!'})
        self.assertEqual(resp.context['form']['full_text'].errors, ['This field is required.'])

    def test_good_post(self):
        self.client.force_login(self.user)
        resp = self.client.post(self.url, self.data)
        self.assertEqual(resp.status_code, 302)
        post = models.Post.objects.order_by('-pub_date')[0]
        post_url = reverse('forum:thread', args=(post.thread.id,))
        post_url = '{0}?postid={1}#{1}'.format(post_url, post.id)
        self.assertEqual(resp['Location'], post_url)

    def test_post_content_escaped_after_formatting(self):
        """
        Ensure, when user creates post, real html tags are escaped,
         and pseudo-tags for formatting are converted to html.
        """
        try:
            import bs4
        except ImportError:
            raise self.skipTest('Beautiful Soup is required for this test')
        self.client.force_login(self.user)
        resp = self.client.post(self.url,
                                {'full_text': '<p>Hello!</p>, [b]Buddy[/b]'}, follow=True)
        post_id = models.Post.objects.order_by('-pub_date')[0].id
        try:
            import lxml
            soup = bs4.BeautifulSoup(resp.content, 'lxml')
        except ImportError:
            soup = bs4.BeautifulSoup(resp.content)
        span = soup.find(id=str(post_id))
        div = span.parent
        div = div.find('div', 'text')
        test_string = div.contents[0]
        # containers are bs objects, strings are strings
        self.assertEqual(test_string, '<p>Hello!</p>, ')
        test_html = div.contents[1]
        tag = soup.div
        self.assertEqual(type(test_html), type(tag))

class TestSignUpView(TestCase):
    fixtures = ['users.json']

    @classmethod
    def setUpTestData(cls):
        cls.data = {
            'username': 'new_user', 'email': 'user@mail.com', 'password1': '123123123',
            'password2': '123123123', 'first_name': 'New', 'last_name': 'User',
        }
        cls.url = reverse('forum:sign_up')


    def test_authenticated_user_redirected(self):
        usr = User.objects.get(username='Lana')
        self.client.force_login(usr)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], reverse('forum:profile'))
        resp = self.client.post(self.url, self.data)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], reverse('forum:profile'))

    def test_works_for_anonymous_user(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        resp = self.client.post(self.url, self.data)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], reverse('forum:registration_success'))
        usr = User.objects.get(username=self.data['username'])
        client_id = self.client.session['_auth_user_id']
        self.assertEqual(str(client_id), str(usr.id))


































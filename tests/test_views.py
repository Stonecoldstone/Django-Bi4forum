from django.test import TestCase
from django.contrib.auth.models import User
from forum import models
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.conf import settings
from .data import validation_errors
import re
import random
from django.core import mail
import urllib.parse as parse
import unittest
try:
    import bs4
except ImportError:
    bs4_imported = False
else:
    bs4_imported = True
try:
    import lxml
except ImportError:
    lxml_imported = False
else:
    lxml_imported = True
skip_reason = 'Beautiful Soup is required for this test.'


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
        thread = models.Thread.objects.get(id=650)
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
        thread = models.Thread.objects.get(id=651)
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
        # test that inactive user doesn't see link
        usr = User.objects.get(username='user_inactive')
        self.client.force_login(usr)
        self.assertNotContains(response, link, html=True)
        # active user
        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertContains(response, link, html=True)


class TestThreadView(TestCase):
    fixtures = ['users.json', 'forum_testdata.json']

    def test_returns_200(self):
        response = self.client.get(reverse('forum:thread', args=(650,)))
        self.assertEqual(response.status_code, 200)

    def test_raises_400_when_nonexistent(self):
        with self.assertRaises(ObjectDoesNotExist):
            models.Thread.objects.get(id=1000)
        response = self.client.get(reverse('forum:thread', args=(1000,)))
        self.assertEqual(response.status_code, 404)

    def test_post_form_availability(self):
        url = reverse('forum:thread', args=(650,))
        form_html = '<form id="post" class="post" action="{}" method="post">'
        form_html = form_html.format(url)
        resp = self.client.get(url)
        self.assertNotContains(resp, form_html)
        # test inactive user
        usr = User.objects.get(username='user_inactive')
        self.client.force_login(usr)
        resp = self.client.get(url)
        self.assertNotContains(resp, form_html)
        # finally test active user
        usr = User.objects.get(username='Lana')
        self.client.force_login(usr)
        resp = self.client.get(url)
        self.assertContains(resp, form_html)





class TestThreadViewPost(TestCase):
    fixtures = ['users.json', 'forum_testdata.json']

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.get(username='Lana')
        cls.data = {'full_text': 'Hello!'}
        cls.url = reverse('forum:thread', args=(650,))

    def test_anonymous_redirected(self):
        """
        Ensure anonymous users are redirected to login page.
        """
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse(settings.LOGIN_URL))
        # expected_url = reverse(settings.LOGIN_URL)
        # self.assertRedirects(response, expected_url)

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
        self.assertFormError(resp, 'form', 'full_text', validation_errors['required'])


    def test_good_post(self):
        self.client.force_login(self.user)
        resp = self.client.post(self.url, self.data)
        self.assertEqual(resp.status_code, 302)
        post = models.Post.objects.order_by('-pub_date')[0]
        post_url = reverse('forum:thread', args=(post.thread.id,))
        post_url = '{0}?postid={1}#{1}'.format(post_url, post.id)
        self.assertEqual(resp['Location'], post_url)

    @unittest.skipUnless(bs4_imported, reason=skip_reason)
    def test_post_content_escaped_after_formatting(self):
        """
        Ensure, when user creates post, real html tags are escaped,
         and pseudo-tags for formatting are converted to html.
        """
        # try:
        #     import bs4
        # except ImportError:
        #     raise self.skipTest('Beautiful Soup is required for this test')
        self.client.force_login(self.user)
        resp = self.client.post(self.url,
                                {'full_text': '<p>Hello!</p>, [b]Buddy[/b]'}, follow=True)
        post_id = models.Post.objects.order_by('-pub_date')[0].id
        # try:
        #     import lxml
        #     soup = bs4.BeautifulSoup(resp.content, 'lxml')
        # except ImportError:
        if lxml_imported:
            soup = bs4.BeautifulSoup(resp.content, 'lxml')
        else:
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

class TestSignUp(TestCase):
    fixtures = ['users.json']

    def setUp(self):
        self.data = {
            'username': 'UseR123_@.+', 'email': 'user@mail.com', 'password1': '123123123',
            'password2': '123123123', 'first_name': 'New', 'last_name': 'User',
        }
        self.url = reverse('forum:sign_up')

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
        usr = User.objects.latest('date_joined')
        client_id = self.client.session['_auth_user_id']
        self.assertEqual(str(client_id), str(usr.id))
        # assert userprofile is created
        try:
            profile = usr.userprofile
        except ObjectDoesNotExist:
            self.fail('UserProfile model was not created.')

    def test_long_username_error(self):
        # max length - 20 symbols
        length = 21
        self.data['username'] = 'a' * length
        resp = self.client.post(self.url, self.data)
        self.assertEqual(resp.status_code, 200)
        error_string = validation_errors['max_length'].format(length)
        self.assertFormError(resp, 'form', 'username', error_string)

    def test_missed_username_error(self):
        # username field is required
        self.data['username'] = ''
        resp = self.client.post(self.url, self.data)
        self.assertEqual(resp.status_code, 200)
        self.assertFormError(resp, 'form', 'username', validation_errors['required'])

    def test_bad_username_error(self):
        # username contains only permitted symbols
        for symb in '!№;%:?*()абв':
            newdata = self.data.copy()
            newdata['username'] += symb
            resp = self.client.post(self.url, newdata)
            self.assertEqual(resp.status_code, 200)
            self.assertFormError(resp, 'form', 'username',
                                 validation_errors['invalid_chars'])

    def test_username_not_unique(self):
        self.data['username'] = 'admin'
        resp = self.client.post(self.url, self.data)
        self.assertEqual(resp.status_code, 200)
        self.assertFormError(resp, 'form', 'username',
                             validation_errors['username_exists'])

    def test_missed_password_error(self):
        passwd_fields = ('password1', 'password2')
        for f in passwd_fields:
            self.data[f] = ''
        resp = self.client.post(self.url, self.data)
        self.assertEqual(resp.status_code, 200)
        for f in passwd_fields:
            self.assertFormError(resp, 'form', f, validation_errors['required'])

    def test_password_mismatch_error(self):
        self.data['password2'] = '123123321'
        resp = self.client.post(self.url, self.data)
        self.assertEqual(resp.status_code, 200)
        self.assertFormError(resp, 'form', 'password2', validation_errors['mismatch'])

    def test_missed_email_error(self):
        self.data['email'] = ''
        resp = self.client.post(self.url, self.data)
        self.assertEqual(resp.status_code, 200)
        self.assertFormError(resp, 'form', 'email', validation_errors['required'])


class TestEmailConfirmation(TestCase):
    fixtures = ['users.json', 'forum_testdata.json']

    def setUp(self):
        self.data = {
            'username': 'new_user', 'password1': '123123123',
            'password2': '123123123', 'email': 'test@mail.com',
        }
        self.resp = self.client.post(reverse('forum:sign_up'), self.data)
        self.user = User.objects.latest('date_joined')

    def test_mail_and_user_match(self):
        self.assertEqual(self.resp.status_code, 302)
        self.assertEqual(self.user.email, self.data['email'])
        self.assertTrue(mail.outbox)
        mail_inst = mail.outbox[0]
        # ensure mail sending function works fine
        self.assertEqual(mail_inst.to[0], self.data['email'])
        self.assertEqual(mail_inst.from_email, settings.EMAIL_HOST_USER)

    def test_random_keys_raise_404(self):
        for i in range(10):
            key = random.SystemRandom().getrandbits(32)
            if key != self.user.userkey.key:
                url = reverse('forum:email_confirmation', args=(self.user.id, key))
                resp = self.client.get(url)
                self.assertEqual(resp.status_code, 404)

    def test_email_confirmation_activates_user(self):
        self.assertFalse(self.user.is_active)
        msg = mail.outbox[0].body
        match = re.search(r'(http://\S+)', msg)
        if match:
            url = match.group()
        else:
            self.fail('Cannot find url in the mail body.')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)


class TestNewThreadView(TestCase):
    fixtures = ['users.json', 'forum_testdata.json']

    def setUp(self):
        self.user = User.objects.get(username='Lana')
        self.data = {
            'thread_title': 'Hello!',
            'full_text': 'Hello dudes!',
                    }
        self.url = reverse('forum:new_thread', args=(1,))

    def test_anonymous_redirected(self):
        """
        Ensure anonymous users are redirected to login page.
        """
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, 302)
        parsed_url = parse.urlsplit(response['Location'])
        self.assertEqual(parsed_url.path, reverse(settings.LOGIN_URL))

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

    def test_bad_subforum_id(self):
        # test that url with non-existent subforum id raises 404
        self.client.force_login(self.user)
        with self.assertRaises(ObjectDoesNotExist):
            models.SubForum.objects.get(id=500)
        bad_url = reverse('forum:new_thread', args=(500,))
        resp = self.client.post(bad_url, self.data)
        self.assertEqual(resp.status_code, 404)

    def test_empty_fields_error(self):
        self.client.force_login(self.user)
        for key in self.data:
            new_data = self.data.copy()
            new_data[key] = ''
            resp = self.client.post(self.url, new_data)
            self.assertFormError(resp, 'form', key, validation_errors['required'])

    def test_title_not_unique_error(self):
        self.client.force_login(self.user)
        self.data['thread_title'] = 'West Coast'
        resp = self.client.post(self.url, self.data)
        self.assertEqual(resp.status_code, 200)
        self.assertFormError(resp, 'form', 'thread_title',
                             validation_errors['title_exists'])

    def test_good_thread(self):
        self.client.force_login(self.user)
        resp = self.client.post(self.url, self.data)
        self.assertEqual(resp.status_code, 302)
        thread = models.Thread.objects.latest('pub_date')
        thread_url = reverse('forum:thread', args=(thread.id,))
        thread_url = '{0}?postid={1}#{1}'.format(thread_url, thread.id)
        self.assertEqual(resp['Location'], thread_url)

    @unittest.skipUnless(bs4_imported, reason=skip_reason)
    def test_thread_content_escaped_after_formatting(self):
        """
        Ensure, when user creates thread, real html tags are escaped,
         and pseudo-tags for formatting are converted to html.
        """
        self.client.force_login(self.user)
        self.data['full_text'] = '<p>Hello!</p>, [b]Buddy[/b]'
        resp = self.client.post(self.url, self.data, follow=True)
        thread_id = models.Thread.objects.latest('pub_date').id
        if lxml_imported:
            soup = bs4.BeautifulSoup(resp.content, 'lxml')
        else:
            soup = bs4.BeautifulSoup(resp.content)
        span = soup.find(id=str(thread_id))
        div = span.parent
        div = div.find('div', 'text')
        test_string = div.contents[0]
        # containers are bs objects, strings are strings
        self.assertEqual(test_string, '<p>Hello!</p>, ')
        test_html = div.contents[1]
        tag = soup.div
        self.assertEqual(type(test_html), type(tag))

class TestSearchView(TestCase):
    fixtures = ['users.json', 'forum_testdata.json']

    def setUp(self):
        self.data = {'search': '', 'user': '', 'search_by': 'pt', 'sort_by': 'p'}
        self.url = reverse('forum:search')

    def test_empty_fileds_error(self):
        resp = self.client.get(self.url, self.data)
        self.assertFormError(resp, 'form', None, validation_errors['empty_search'])


    def test_bad_input_radiobutton_fields_errors(self):
        self.data['search'] = 't'
        fields = ('search_by', 'sort_by')
        for f in fields:
            self.data[f] = ''
            resp = self.client.get(self.url, self.data)
            self.assertFormError(resp, 'form', f, validation_errors['required'])
        #test junk input
        for f in fields:
            self.data[f] = 'blabla'
            resp = self.client.get(self.url, self.data)
            error = validation_errors['invalid_choice'].format(self.data[f])
            self.assertFormError(resp, 'form', f, error)


    def test_raw_text_is_searched(self):
        usr = User.objects.get(username='Lana')
        sub = models.SubForum.objects.get(id=1)
        strings = ('[b]Random[/b]', 'Random')
        new_thread = models.Thread(user=usr, subforum=sub, thread_title='New Thread',
                                   full_text=strings[0])
        new_thread.save()
        self.data['search'] = strings[0]
        resp = self.client.get(self.url, self.data)
        self.assertFalse(resp.context['query'])
        self.data['search'] = strings[1]
        resp = self.client.get(self.url, self.data)
        self.assertQuerysetEqual(resp.context['query'], ['<Thread: New Thread>'])

    def test_search_by_pt(self):
        strings = {
                      'west coast': [
                          '<Post: Lana: Down on the West...>', '<Thread: Coast West>',
                          '<Post: Lana: Down on the West...>', '<Thread: West Coast>',
                      ],
                      'test': [
                          '<Thread: Test thread>', '<Post: admin: test post test...>'
                      ],
        }
        for s, q in strings.items():
            self.data['search'] = s
            resp = self.client.get(self.url, self.data)
            self.assertQuerysetEqual(resp.context['query'], q, ordered=False)

    def test_search_by_t(self):
        strings = {
            'west coast': ['<Thread: West Coast>', '<Thread: Coast West>'],
            'test': ['<Thread: Test thread>'],
        }
        self.data['search_by'] = 't'
        for s, q in strings.items():
            self.data['search'] = s
            resp = self.client.get(self.url, self.data)
            self.assertQuerysetEqual(resp.context['query'], q, ordered=False)

    def test_search_by_p(self):
        strings = {
            'west coast': [
                '<Post: Lana: Down on the West...>',
                '<Post: Lana: Down on the West...>'
            ],
            'test': ['<Post: admin: test post test...>'],
        }
        self.data['search_by'] = 'p'
        for s, q in strings.items():
            self.data['search'] = s
            resp = self.client.get(self.url, self.data)
            self.assertQuerysetEqual(resp.context['query'], q, ordered=False)

    def test_search_by_username(self):
        self.data['search'] = 't'
        usernames = 'Lana', 'admin'
        for name in usernames:
            self.data['user'] = name
            resp = self.client.get(self.url, self.data)
            for item in resp.context['query']:
                self.assertEqual(item.user.username, name)

    def test_sort_by_date(self):
        self.data['search'] = 't'
        resp = self.client.get(self.url, self.data)
        query = resp.context['query']
        prev_item = query[0]
        for item in query[1:]:
            self.assertGreaterEqual(prev_item.pub_date, item.pub_date)
            prev_item = item

    def test_sory_by_rating(self):
        self.data['search'] = 't'
        self.data['sort_by'] = 'rt'
        resp = self.client.get(self.url, self.data)
        query = resp.context['query']
        prev_item = query[0]
        for item in query[1:]:
            self.assertGreaterEqual(prev_item.rating, item.rating)
            prev_item = item

    def test_search_subforums(self):
        self.data['search'] = 't'
        sub_num = 1
        self.data['subforums'] = sub_num
        resp = self.client.get(self.url, self.data)
        query = resp.context['query']
        for item in query:
            if hasattr(item, 'subforum'):
                self.assertEqual(item.subforum.id, sub_num)
            else:
                self.assertEqual(item.thread.subforum.id, sub_num)
        sub_num = (1, 2)
        self.data['subforums'] = sub_num
        resp = self.client.get(self.url, self.data)
        query = resp.context['query']
        for item in query:
            if hasattr(item, 'subforum'):
                self.assertIn(item.subforum.id, sub_num)
            else:
                self.assertIn(item.thread.subforum.id, sub_num)


class TestProfileView(TestCase):
    fixtures = ['users.json', 'forum_testdata.json']

    def setUp(self):
        self.url = reverse('forum:profile')
        self.usr = User.objects.get(username='Lana')
        self.client.force_login(self.usr)

    def test_profile_of_right_user_is_displayed(self):
        resp = self.client.get(self.url)
        prof_user = resp.context['user']
        self.assertEqual(prof_user.id, self.usr.id)
        usr = User.objects.get(username='admin')
        url = reverse('forum:profile', args=(usr.id,))
        resp = self.client.get(url)
        prof_user = resp.context['user']
        self.assertEqual(prof_user.id, usr.id)

    def test_last_threads(self):
        sub = models.SubForum.objects.get(id=1)
        for i in range(10):
            t = models.Thread(subforum=sub, user=self.usr, thread_title=i, full_text=str(i))
            t.save()
        test_query = ['<Thread: {}>'.format(i) for i in range(9, -1, -1)]
        resp = self.client.get(self.url)
        self.assertQuerysetEqual(resp.context['last_threads'], test_query)

    def test_last_posts(self):
        thread = models.Thread.objects.get(id=650)
        for i in range(10):
            p = models.Post(user=self.usr, thread=thread, full_text=str(i))
            p.save()
        test_query = ['<Post: Lana: {}>'.format(i) for i in range(9, -1, -1)]
        resp = self.client.get(self.url)
        self.assertQuerysetEqual(resp.context['last_posts'], test_query)

    def test_mail_confirmation_button(self):
        # ensure active user doesn't see that button in his own profile
        html = '<input class="excluded" type="submit" value="Click to resend a confirmation mail"/>'
        resp = self.client.get(self.url)
        self.assertNotContains(resp, html, html=True)
        # ensure active user doesn't see that button in inactive user's profile
        usr = User.objects.get(username='user_inactive')
        self.assertFalse(usr.is_active)
        url = reverse('forum:profile', args=(usr.id,))
        resp = self.client.get(url)
        self.assertNotContains(resp, html, html=True)
        # ensure inactive user sees button in his profile
        self.client.force_login(usr)
        resp = self.client.get(self.url)
        self.assertContains(resp, html, html=True)
        # ensure inactive user doesn't see button in active user's profile
        url = reverse('forum:profile', args=(self.usr.id,))
        resp = self.client.get(url)
        self.assertNotContains(resp, html, html=True)

    @unittest.skipUnless(bs4_imported, reason=skip_reason)
    def test_signature_is_escaped_after_formatting(self):
        self.usr.userprofile.signature = '<b>Hello</b>[b]Buddy[/b]'
        resp = self.client.get(self.url)
        if lxml_imported:
            soup = bs4.BeautifulSoup(resp.content, 'lxml')
        else:
            soup = bs4.BeautifulSoup(resp.content)
        # span = soup.find(id=str(post_id))
        # div = span.parent
        # div = div.find('div', 'text')
        # test_string = div.contents[0]
        # # containers are bs objects, strings are strings
        # self.assertEqual(test_string, '<p>Hello!</p>, ')
        # test_html = div.contents[1]
        # tag = soup.div
        # self.assertEqual(type(test_html), type(tag))




































































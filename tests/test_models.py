from django.test import TestCase
from forum import models
from django.contrib.auth.models import User

class TestModelsMethods(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='testuser',
                                                        password='123123123',
                                                        email='test@gmail.com')
        cls.cat = models.Category.objects.create(title='First', precedence=1)
        cls.sub = models.SubForum.objects.create(category=cls.cat, title='First in first', precedence=2)
        for i in range(10):
            thread = models.Thread(subforum=cls.sub, user=cls.user,
                                   thread_title='{} Thread'.format(i),
                                   full_text='{} Post'.format(i))
            thread.save()
            for j in range(10):
                post = models.Post(thread=thread, user=cls.user,
                                   full_text='{} Thread {} Post'.format(i, j))
                post.save()
    def test_add_atts_method(self):
        subforum = models.SubForum.objects.filter(title='First in first')
        subforum = subforum.add_atts()
        subforum = subforum[0]
        last = models.Thread.objects.get(thread_title='9 Thread')
        last_post = models.Post.objects.get(full_text='9 Thread 9 Post')
        with self.subTest():
            self.assertEqual(subforum.thread_count, 10)
        with self.subTest():
            self.assertEqual(subforum.post_count, 100)
        with self.subTest():
            self.assertEqual(subforum.last_thread, last)
        self.assertEqual(subforum.last_post, last_post)


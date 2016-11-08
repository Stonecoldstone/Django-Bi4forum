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



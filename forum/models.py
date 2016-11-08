from textwrap import shorten

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.files import File
from django.core.urlresolvers import reverse
from django.db import models
from django.utils import timezone

from . import functions
from . import settings as forum_settings
from .templatetags.forum_tags import replace_markdown


class Category(models.Model):
    title = models.CharField(max_length=200)
    precedence = models.IntegerField(default=0)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['precedence']
        verbose_name_plural = 'categories'


class SubForum(models.Model):
    title = models.CharField(max_length=200)
    description = models.CharField(max_length=300, blank=True, null=True, default='')
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    precedence = models.IntegerField(default=0)
    create_time = models.DateTimeField(auto_now_add=True)
    # objects = SubForumQuerySet.as_manager()

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['category__precedence', 'precedence']


class ThreadPostAbstract(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    pub_date = models.DateTimeField(auto_now_add=True)
    edit_date = models.DateTimeField(default=timezone.now)
    full_text = models.TextField()
    raw_text = models.TextField()

    def save(self, *args, **kwargs):
        text_diff = self.text_diff()
        # just_created = self.pk is None
        if text_diff:
            self.raw_text = str(replace_markdown(self.full_text,
                                                 delete=True,
                                                 autoescape=False))
        if text_diff or self.title_diff():
            self.edit_date = timezone.now()
        super(ThreadPostAbstract, self).save(*args, **kwargs)

    def is_edited(self):
        return self.pub_date < self.edit_date

    def text_diff(self):
        try:
            orig = self.__class__.objects.get(pk=self.pk)
        except ObjectDoesNotExist:
            return True
        return self.full_text != orig.full_text

    def title_diff(self):
        return False

    def get_rating(self):
        res = self.users_liked.count() - self.users_disliked.count()
        return res

    def is_liked(self, user):
        query = self.users_liked.filter(id=user.id).exists()
        return query

    def is_disliked(self, user):
        query = self.users_disliked.filter(id=user.id).exists()
        return query

    class Meta:
        abstract = True


class Thread(ThreadPostAbstract):
    thread_title = models.CharField(max_length=70, verbose_name='title')
    subforum = models.ForeignKey(SubForum, on_delete=models.CASCADE)
    is_attached = models.BooleanField(default=False)
    post_add_date = models.DateTimeField(default=timezone.now)
    users_liked = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='threads_liked')
    users_disliked = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='threads_disliked')
    # objects = CustomQuerySet.as_manager()

    def __str__(self):
        return self.thread_title

    def get_absolute_url(self):
        string = '{0}?postid={1}#{1}'
        url = reverse('forum:thread', args=(self.id,))
        return string.format(url, self.id)

    def title_diff(self):
        orig = Thread.objects.get(pk=self.pk)
        return self.thread_title != orig.thread_title

    class Meta:
        ordering = ['-post_add_date', '-pub_date']


class Post(ThreadPostAbstract):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE)
    users_liked = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='posts_liked')
    users_disliked = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='posts_disliked')

    def __str__(self):
        text = shorten(self.full_text, 20, placeholder='...')
        return '%s: %s' % (self.user, text)

    def save(self, *args, **kwargs):
        if self.pk is None:
            thrd_id = self.thread.id
            Thread.objects.filter(id=thrd_id).update(post_add_date=timezone.now())
        super(Post, self).save(*args, **kwargs)

    def get_absolute_url(self):
        thread_id = self.thread.id
        return '{0}?postid={1}#{1}'.\
            format(reverse('forum:thread', args=(thread_id,)), self.id)


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    signature = models.TextField(default='', max_length=300, blank=True, null=True)
    avatar = models.ImageField(max_length=200, upload_to='avatars', blank=True,
                               null=True)

    new_email = models.EmailField(default='', blank=True, null=True)

    def substitute_mail(self):
        if self.new_email:
            self.user.email = self.new_email
            self.new_email = ''
            self.user.save()
            self.save()

    def save(self, *args, **kwargs):
        if self.avatar:
            if self.pk is not None:
                orig = UserProfile.objects.get(pk=self.pk)
                orig = orig.avatar
            else:
                orig = False
            if orig != self.avatar:
                size = forum_settings.AVATAR_SIZE
                resized_img = functions.resize(size, bytes=self.avatar.read())
                name = self.avatar.name
                orig.delete(save=False)
                file = File(resized_img)
                self.avatar.save(name, file, save=False)
            # check if avatars are compared at all:
            # else:
            #     raise ValueError
        super(UserProfile, self).save(*args, **kwargs)

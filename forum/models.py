from django.db import models
from django.utils import timezone
from django.conf import settings
from django.core.urlresolvers import reverse
from textwrap import shorten
from . import functions
from django.core.files import File


class Category(models.Model):
    title = models.CharField(max_length=200)
    precedence = models.IntegerField(default=0)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['precedence']
        verbose_name_plural = 'categories'


class SubForumQuerySet(models.QuerySet):
    def add_atts(self):
        self = self.annotate(
            thread_count=models.Count('thread', distinct=True),
            post_count=models.Count('thread__post',
                             distinct=True)
        )
        for entry in self:
            # entry.post_count -= entry.thread_count  # ocherednoy kostil'\ add custom manager or smth
            try:
                entry.last_thread = entry.thread_set.all()[0]
            except IndexError:
                entry.last_thread = None
                entry.last_post = None
                continue
            try:
                entry.last_post = entry.last_thread.post_set.order_by('-pub_date')[0]
            except IndexError:
                entry.last_post = entry.last_thread
        return self
    add_atts.queryset_only = True

class SubForum(models.Model):
    title = models.CharField(max_length=200)
    description = models.CharField(max_length=300, blank=True, null=True, default='')
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    precedence = models.IntegerField(default=0)
    create_time = models.DateTimeField(auto_now_add=True)
    objects = SubForumQuerySet.as_manager()

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['category__precedence', 'precedence']


class ThreadPostAbstract(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    pub_date = models.DateTimeField(auto_now_add=True)
    edit_date = models.DateTimeField(default=timezone.now)
    rating = models.IntegerField(default=0)
    full_text = models.TextField()
    raw_text = models.TextField()

    def save(self, *args, **kwargs):
        self.raw_text = functions.replace_tags(self.full_text, delete=True)
        super(ThreadPostAbstract, self).save(*args, **kwargs)

    def is_edited(self):
        boolean = False
        if self.edit_date > self.pub_date:
            boolean = True
        return boolean

    # def is_liked(self, user):
    #     query = self.users_liked.filter(id=user.id)
    #     res = False
    #     if query:
    #         res = True
    #     return res
    #
    # def is_disliked(self, user):
    #     query = self.users_disliked.filter(id=user.id)
    #     res = False
    #     if query:
    #         res = True
    #     return res

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

    # def get_absolute_url(self):
    #     return reverse('forum:thread', args=(self.id,))
    def get_absolute_url(self):
        string = '{0}?postid={1}#{1}'
        url = reverse('forum:thread', args=(self.id,))
        return string.format(url, self.id)

    class Meta:
        ordering = ['-post_add_date', '-pub_date']


class Post(ThreadPostAbstract):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE)
    users_liked = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='posts_liked')
    users_disliked = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='posts_disliked')
    # full_text = models.TextField()
    # is_thread = models.BooleanField(default=False)

    def __str__(self):
        text = shorten(self.full_text, 20, placeholder='...')
        return '%s: %s' % (self.user, text)

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.thread.post_add_date = timezone.now()
            self.thread.save()
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
    def save(self, *args, **kwargs):
        if self.avatar:
            if self.pk is not None:
                orig = UserProfile.objects.get(pk=self.pk)
                orig = orig.avatar
            else:
                orig = False
            if orig != self.avatar:
                size = (200, 200)
                resized_img = functions.resize(size, bytes=self.avatar.read())
                name = self.avatar.name
                orig.delete(save=False)
                file = File(resized_img)
                self.avatar.save(name, file, save=False)
        super(UserProfile, self).save(*args, **kwargs)



class UserKey(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    key = models.CharField(max_length=50)
    email = models.EmailField(default='')




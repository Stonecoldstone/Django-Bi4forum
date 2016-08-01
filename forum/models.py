from django.db import models
from django.utils import timezone
from django.conf import settings
from django.core.urlresolvers import reverse


class Category(models.Model):
    title = models.CharField(max_length=200)
    precedence = models.IntegerField(default=0)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['precedence']


class SubForumQuerySet(models.QuerySet):
    def add_atts(self):
        self = self.annotate(
            thread_count=models.Count('thread', distinct=True),
            post_count=models.Count('thread__post',
                             distinct=True)
        )
        for entry in self:
            entry.post_count -= entry.thread_count  # ocherednoy kostil'\ add custom manager or smth
            try:
                entry.last_thread = entry.thread_set.all()[0]
            except IndexError:
                entry.last_thread = None
                entry.last_post = None
                continue
            entry.last_post = entry.last_thread.post_set.order_by('-pub_date')[0]
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
    edit_date = models.DateTimeField(auto_now=True)
    rating = models.IntegerField(default=0)

    class Meta:
        abstract = True

# class CustomQuerySet(models.QuerySet):
#     def add_atts(self, posts_on_page=10, pages_displayed=3):
#         for t in self:
#             num_posts = t.post_set.count()
#             range_val = math.ceil(num_posts / posts_on_page)
#             thread_pages = list(range(1, range_val + 1))
#             thread_pages = thread_pages[:pages_displayed]
#             t.last_page = range_val
#             t.thread_pages = thread_pages
#             t.posts_num = num_posts - 1
#             t.last_post = t.post_set.order_by('-pub_date')[0]
#         return self
#     add_atts.queryset_only = True


class Thread(ThreadPostAbstract):
    thread_title = models.TextField(max_length=70)
    subforum = models.ForeignKey(SubForum, on_delete=models.CASCADE)
    is_attached = models.BooleanField(default=False)
    post_add_date = models.DateTimeField(default=timezone.now)
    # objects = CustomQuerySet.as_manager()

    def __str__(self):
        return self.thread_title

    def get_absolute_url(self):
        return reverse('forum:thread', args=(self.id, 1))

    class Meta:
        ordering = ['-post_add_date', '-pub_date']


class Post(ThreadPostAbstract):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE)
    full_text = models.TextField()
    is_thread = models.BooleanField(default=False)

    def __str__(self):
        return '%s: %s...' % (self.user, self.full_text[:15])

    def save(self, *args, **kwargs):
        thread = self.thread
        thread.post_add_date = timezone.now()
        thread.save()
        super(Post, self).save(*args, **kwargs)

    def get_absolute_url(self):
        thread_id = self.thread.id
        return '{0}?postid={1}#{1}'.\
            format(reverse('forum:thread', args=(thread_id,)), self.id)

    def print_profile(self):
        return self.full_text[:25]

    # class Meta:
    #     permissions = (
    #         ('change_post_instance', 'Can change the post'),
    #     )


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    signature = models.TextField(default='', blank=True, null=True)
    avatar = models.ImageField(max_length=200, upload_to='avatars', blank=True,
                               null=True)

class UserKey(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    key = models.CharField(max_length=50)
    email = models.EmailField(default='')




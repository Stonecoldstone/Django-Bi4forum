from django.contrib import admin
from .models import Category, SubForum, Thread, Post, UserProfile
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User


class PostInline(admin.StackedInline):
    model = Post
    exclude = ('raw_text',)



class ThreadAdmin(admin.ModelAdmin):
    inlines = (PostInline,)
    date_hierarchy = 'pub_date'
    readonly_fields = ('post_add_date', 'pub_date', 'edit_date')
    fields = (
        ('user', 'subforum'), 'is_attached', 'thread_title',
        'full_text', 'pub_date', 'edit_date', 'post_add_date'
    )

    def title_display(self, obj):
        return '%s' % obj.thread_title[:30]
    title_display.short_description = 'title'
    list_display = ('title_display', 'user', 'subforum', 'pub_date', 'post_add_date')
    search_fields = ('thread_title', 'user__username',)



class PostAdmin(admin.ModelAdmin):
    date_hierarchy = 'pub_date'
    readonly_fields = ('pub_date', 'edit_date')
    fields = (
        ('user', 'thread'), 'full_text', 'pub_date', 'edit_date',
    )

admin.site.register(Post, PostAdmin)


models = [Category, SubForum]
for m in models:
    admin.site.register(m)

admin.site.register(Thread, ThreadAdmin)


class ProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'users profiles'


class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_active')


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
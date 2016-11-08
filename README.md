## Django Bi4forum
Bi4forum is a simple forum application, which I was developing while learning django.

It implements basic forum functions, such as search, custom markdown, user profile, listing subforums, threads, posts etc.
It is hosted at https://Bi4.pythonanywhere.com, so there you can check almost every feature of it.

It was built under python 3.5 and Django 1.9.

### Required modules
* [Pillow](https://pillow.readthedocs.io/) is required for resizing and cropping avatars uploaded by users,
as well as for django ImageField to work.
* [Haystack](http://haystacksearch.org/) and any **search engine** supported by haystack (I'm using Whoosh on pythonanywhere)
are required by search view, as it uses haystack search queries. Bi4forum contains a file with index classes required by haystack,
but you would need to specify settings appropriate for a preferred search engine.
* **Django default apps** - every app that is included by default in **INSTALLED_APPS** setting when creating a new project
is used by some part of the forum. Probably you can omit the admin app, although it is quite convenient.

### Installation
1. Download this repo.
2. In a shell execute **$ pip install *path-to-repo*/dist/bi4forum-0.1.tar.gz**.
3. In your project's **settings.py** file add **'forum'** into **INSTALLED_APPS**.
4. In your project's **urls.py** file include urls from the forum into **urlpatterns** list, for example:  
    ```
    from django.conf.urls import url, include
    from django.contrib import admin
    urlpatterns = [
        url(r'^admin/', admin.site.urls),
        url(r'^forum/', include('forum.urls')),
        ]
    ```
5. In order to be sure that all forum features would work correctly and not crash, check that the following settings
 are set properly:
   * Email settings (**EMAIL_HOST**, **EMAIL_HOST_USER**, **EMAIL_HOST_PASSWORD**, **EMAIL_PORT**, **EMAIL_USE_TLS**, **EMAIL_USE_SSL**)

   * **MEDIA_URL**
   * **MEDIA_ROOT**
   * **[Haystack settings](http://django-haystack.readthedocs.io/en/v2.5.0/settings.html)**
6. Execute **$ python *project-directory*/manage.py migrate.**

### Settings
The following are forum-specific settings and their defaults:  

**FORUM_NAME** - name of the forum, used in a couple of places  
    Default: 'Bi4forum'

**FILE_MAX_SIZE** - max size for an avatar uploaded by user specified in bytes  
    Default: 1024 * 1024 (1 Mb)

**POSTS_ON_PAGE** - number of posts listed on a page  
    Default: 20

**THREADS_ON_PAGE** - number of threads listed on a page  
    Default: 20

**AVATAR_SIZE** - width and height that would be used to resize and crop an avatar before storing; specified in pixels  
    Default: (200, 200)

**IMG_SIZE** - max-width and max-height css attributes, that would be applied to images in a text; specified in pixels  
    Default: (800, 600)







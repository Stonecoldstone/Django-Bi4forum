# import django
# import sys
# import os
# sys.path.insert(0, 'forumsite')
# os.environ['DJANGO_SETTINGS_MODULE'] = 'forumsite.settings'
# django.setup()
# from forum.functions import replace_tags
post_tags = (
    ('''
    [b]I[/b] [i][lt]can[/lt] [u]see[/u] my baby[/i] [center]swingin'[/center]
    [a=/main_page/]His Parliament's[/a] [q]on[/q][size=25] fire and his[/size] hands are up
    [color=blue]On the balcony and I'm singing[/color]
    [video]/static/LRDedit.MP4[/video]
    Ooh, baby, ooh, baby, I'm in love
    [img]/static/avatar.jpg[/img]
    ''',
    '''
    <b>I</b> <i><span style="text-decoration:line-through">can</span> <span style="text-decoration:underline">see</span> my baby</i> <p style="text-align:center">swingin'</p>
    <a href="/main_page/">His Parliament's</a> <blockquote>on</blockquote><span style="font-size:25px"> fire and his</span> hands are up
    <span style="color:blue">On the balcony and I'm singing</span>
    <video width="560" height="420" controls><source src="/static/LRDedit.MP4" type=video/webm><source src="/static/LRDedit.MP4" type=video/ogg><source src="/static/LRDedit.MP4" type=video/mp4>Your browser does not support the video tag.</video>
    Ooh, baby, ooh, baby, I'm in love
    <img src="/static/avatar.jpg" alt="Image"/>
    '''),
)

from embed_video.backends import VideoBackend
import re

class CustomBackend(VideoBackend):
    re_detect = re.compile(r'^(http(s)?://)?.+')
    re_code = re.compile(r'^(http(s)?://)?(?P<code>.+)')
    pattern_url = '{protocol}://{code}'
    pattern_thumbnail_url = '{protocol}://{code}'
    template_name = 'forum/video/backend.html'
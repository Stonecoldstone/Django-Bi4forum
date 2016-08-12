from unittest import TestCase
from forum import functions
import random


class TestReplaceTags(TestCase):

    def test_replace_tags_func(self):
        tag_list = (
            ('[b]{}[/b]', '<b>{}</b>'), ('[i]{}[/i]', '<i>{}</i>'),
            ('[lt]{}[/lt]', '<span style="text-decoration:line-through">{}</span>'),
            ('[u]{}[/u]', '<span style="text-decoration:underline">{}</span>'),
            ('[center]{}[/center]', '<p style="text-align:center">{}</p>'),
            ('[img]{}[/img]', '<img src="{}" alt="Image"/>'),
            (
                '[video]{}[/video]',
                '<video width="560" height="420" controls>'
                '<source src="{0}" type=video/webm>'
                '<source src="{0}" type=video/ogg>'
                '<source src="{0}" type=video/mp4>'
                'Your browser does not support the video tag.'
                '</video>'
            ),
            ('[size=20]{}[/size]', '<span style="font-size:20px">{}</span>'),
            ('[color=red]{}[/color]', '<span style="color:red">{}</span>'),
            ('[q]{}[/q]', '<blockquote>{}</blockquote>'),
        )
        test_text = 'I can see my baby swingin His Parliament\'s on fire and hands are up'
        for i in range(20):
            for j in range(10):
                mark_list = test_text.split(' ')
                html_list = mark_list[:]
                marks, tags = random.choice(tag_list)
                word = random.choice(mark_list)
                index = mark_list.index(word)
                word = marks.format(word)
                mark_list[index] = word
                word = html_list[index]
                word = tags.format(word)
                html_list[index] = word
            func_res = functions.replace_tags(' '.join(mark_list))
            html_list = ' '.join(html_list)
            self.assertEqual(func_res, html_list)




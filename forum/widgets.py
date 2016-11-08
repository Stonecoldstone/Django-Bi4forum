from django.forms import Widget
from django.forms.utils import flatatt
from django.utils.html import format_html


class ForumWidget(Widget):

    def render(self, name, value, attrs=None):
        if value is None:
            value = ''
        final_attrs = self.build_attrs(attrs, name=name)
        return format_html('''<div class="fta_container">
                           <ul class="fta_button_row">
                           </ul>
                           <textarea class="fta_input" {}>{}</textarea>
                           </div>''', flatatt(final_attrs), value)

    class Media:
        css = {
            'all': ('forum_textarea.css',)
        }
        js = ('test.js',)

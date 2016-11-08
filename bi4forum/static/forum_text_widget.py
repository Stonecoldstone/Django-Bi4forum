from django.forms import Widget
from django.forms.utils import flatatt
from django.utils.encoding import force_text
from django.utils.html import format_html

class ForumWidget(Widget):
    def render(self, name, value, attrs=None):
        if value is None:
            value = ''
        final_attrs = self.build_attrs(attrs, type=self.input_type, name=name)
        if value != '':
            # Only add the 'value' attribute if a value is non-empty.
            final_attrs['value'] = force_text(self._format_value(value))
        return format_html('''<div class="fta_container">
                           <ul class="fta_button_row">
                           </ul>
                           <textarea class="fta_input" {}></textarea>
                           </div>''', flatatt(final_attrs))

    class Media:
        css = {
            'all': ('forum_textarea.css',)
        }
        js = ('test.js',)
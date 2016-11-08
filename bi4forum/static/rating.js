$(document).ready(function() {
$('div.message').on('click', 'input', function(event){
var input, formUrl, name, value;
input = $(this)
formUrl = input.parent().attr('action');
name = input.attr('name');
value = input.attr('value');
$.ajax({
url: formUrl,
data: {
[name]: value,
csrfmiddlewaretoken: csrftoken
},
type: 'POST',
dataType: 'json'
}).done(function(json) {
var mapObj = {
'like': 'liked',
'dislike': 'disliked'
};
input.toggleClass(mapObj[name]);
input.siblings('span').html(json.count);
});
event.preventDefault();
});
});
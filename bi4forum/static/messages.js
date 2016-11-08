$(document).ready(function() {
$('a.close').on('click', function(event) {
$(this).parent().removeClass().addClass('hidden');
event.preventDefault();
});
});
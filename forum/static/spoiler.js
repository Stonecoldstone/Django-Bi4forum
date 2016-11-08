$(document).ready(function() {
$('.spoiler').on('click', 'button', function() {
$(this).toggleClass('opened_spoiler');
$(this).next().slideToggle(200);
});
});
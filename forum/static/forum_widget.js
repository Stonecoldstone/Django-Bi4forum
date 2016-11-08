$(document).ready(function() {
    generateLi();
	$('.fta_button_row').on('click', 'li', function(event) {
	mainDelegation.call(this);
	}
	);
//	var colorLi = $('.fta_color');
//	var sizeLi = $('.fta_size');
	var objects = [$('.fta_color'), $('.fta_size')];
	for (var i = 0; i < objects.length; i++) {
		function iterover(i) {
			var obj = objects[i];
			obj.on('mouseenter', function() {
				$(this).find('div').slideDown(100);
			});
			obj.on('mouseleave', function() {
				$(this).find('div').slideUp(100);
			});
		}
		iterover(i);
//	var widget = $('.fta_container');
//	widget.on('focusin', function() {
//	console.log($(this).children());
//	$(this).children().addClass('new_border');
//	});
//    widget.on('focusout', function() {
//    $(this).children().removeClass('new_border');
//    });
}
});
function mainDelegation(event) {
	var obj, objClass, dropdowns, urlgetters, input, start, end, inputValue,
	    firstReplace, patternMapping, newSubstring, newString;
	obj = $(this);
	objClass = obj.attr('class');
	if (objClass === 'fta_color' || objClass === 'fta_size') {
		var target = $(event.target);
		if (target.prop('tagName') === 'SPAN') {
			obj.find('div').slideToggle(100);
			return;
		}
    }
    dropdowns = {
		'color_drop_li': getColor,
		'size_drop_li': getSize,
	    };
	urlgetters = {
		'fta_link': getLink,
		'fta_img': getImage,
		'fta_video': getVideo,
	    };
	input = obj.closest('.fta_button_row').next()
	console.log(input);
	start = input[0].selectionStart;
	end = input[0].selectionEnd;
	inputValue = input.val();
	if (start === end) {
	    firstReplace = ''
	    if (start === 0) {
	    	start, end == inputValue.length;
	    }
	}
	else {
	    firstReplace = inputValue.substring(start, end);
	}
	if (dropdowns.hasOwnProperty(objClass)) {
	    secondReplace = dropdowns[objClass](obj);
	}
	else if (urlgetters.hasOwnProperty(objClass)) {
	    var replaceList = urlgetters[objClass](firstReplace);
	    firstReplace = replaceList[0];
	    if (!(firstReplace)) {
	    	return;
	    }
	    secondReplace = replaceList[1];
	}
	else {
	    secondReplace = '';
	    }
	patternMapping = {
		fta_bold: '[b]%1[/b]',
		fta_italic: '[i]%1[/i]',
		fta_lt: '[lt]%1[/lt]',
		fta_underline: '[u]%1[/u]',
		fta_center: '[center]%1[/center]',
		fta_link: '[a=%1]%2[/a]',
		fta_img: '[img]%1[/img]',
		fta_video: '[video]%1[/video]',
		size_drop_li: '[size=%2]%1[/size]',
		color_drop_li: '[color=%2]%1[/color]',
		fta_quote: '[q]%1[/q]',
		fta_spoiler: '[spoiler]%1[/spoiler]',
	};
	console.log(objClass);
    newSubstring = patternMapping[objClass];
    newSubstring = newSubstring.replace('%1', firstReplace).replace('%2', secondReplace);
    if (firstReplace) {
        caretPos = start + newSubstring.length;
    }
    else {
        caretPos = start + (newSubstring.indexOf(']') + 1);
    }
    newString = inputValue.substring(0, start) + newSubstring + inputValue.substring(end, inputValue.length);
    input.val(newString);
    input.focus();
    input[0].setSelectionRange(caretPos, caretPos);
}

function getSize(obj) {
    var sizeMap = {
	            	'Very small': '10',
	            	'Small': '14',
	            	'Medium': '18',
	            	'Large': '26',
	            	'Very large': '36'
	};
	return sizeMap[obj.html()];
}
function getColor(obj) {
	return obj.html().toLowerCase();
}

function getVideo(value) {
	if (!(value)) {
		value = prompt('Video URL');
	}
	return [value, ''];
}
function getImage(value) {
	if (!(value)) {
		value = prompt('Image URL');
	}
	return [value, ''];
}
function getLink(value) {
	if (!(value)) {
		value = prompt('URL', 'https://www.google.com');
	}
	second = prompt('Link name', 'Link')
	return [value, second];
}

function generateLi() {
var ul = $('.fta_button_row');
 liClassesTitles = [
 ['bold', 'Bold'], ['italic', 'Italic'], ['lt', 'Line through'],
 ['underline', 'Underline'], ['center', 'Centered'], ['link', 'Hyperlink'],
 ['img', 'Image'], ['video', 'Video'], ['size', 'Size'], ['color', 'Color'],
 ['quote', 'Quote'], ['spoiler', 'Spoiler']
 ];
 pos = 0;
 $.each(liClassesTitles, function(ind, sublist) {
 var li = $('<li/>', {
 'class': 'fta_' + sublist[0],
 title: sublist[1]
 });
 ul.append(li);
 var span = $('<span/>');
 span.attr('style', 'background-position:' + pos.toString() + 'px 0px;');
 pos -= 30;
 li.append(span);
 if (sublist[0] === 'size') {
 var div = $('<div class="size_dropdown hidden"></div>');
 li.append(div);
 var sizeUl = $('<ul class="size_dropdown_ul"></ul>');
 div.append(sizeUl);
 valuesList = ['Very small', 'Small', 'Medium', 'Large', 'Very large'];
 $.each(valuesList, function(ind, text) {
 var li = $('<li class="size_drop_li">' + text + '</li>');
 sizeUl.append(li);
 });
 }
 else if (sublist[0] === 'color') {
 var div = $('<div class="color_dropdown hidden"></div>');
 li.append(div);
 var sizeUl = $('<ul class="color_dropdown_ul"></ul>');
 div.append(sizeUl);
 valuesList = ['Red', 'Green', 'Blue', 'White', 'Orange', 'Purple', 'Black'];
 $.each(valuesList, function(ind, text) {
 var li = $('<li class="color_drop_li">' + text + '</li>');
 sizeUl.append(li);
});
}
 });
 }


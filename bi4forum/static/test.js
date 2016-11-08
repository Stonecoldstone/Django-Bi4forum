
function tryIt() {
    generateLi();
	var ul = document.getElementsByClassName('fta_button_row');
	var colorDropdown = document.getElementsByClassName('fta_color');
	var sizeDropdown = document.getElementsByClassName('fta_size');
     // change this shit so event handlers would send "this.getElementsByTagName"
	var varArray = [
	[sizeDropdown, 'size_dropdown'],
	[colorDropdown, 'color_dropdown']
	];

    for (i = 0; i < varArray.length; i++) {
    	function iterover(i) {
    	var subList;
    	subList = varArray[i];
    	addEvent(subList[0], 'mouseenter', function() {
    		show.call(this.getElementsByClassName(subList[1])[0], 'hidden');
    	});
    	addEvent(subList[0], 'mouseleave', function() {
    		hide.call(this.getElementsByClassName(subList[1])[0], 'hidden');
    	});
    	addEvent(subList[0], 'click', function () {
    		showToggle.call(this.getElementsByClassName(subList[1])[0], 'hidden');
    	})
        }
        iterover(i);
    }
    addEvent(ul, 'click', mainDelegation);

}

function addEvent(elem, event, func) {
	for (var i = 0; i < elem.length; i++) {
		elem[i].addEventListener(event, func);
	}
}

function show(class_) {
		child = this
	child.className = child.className.replace(class_, '');

}
function hide(class_) {
		child = this;
	var classes = child.className;
	if (!(classes.includes(class_))) {
		child.className += ' ' + class_;
	}
}

function showToggle(class_) {
	var classes = this.className;
	if (classes.includes(class_)) {
		var newstr = classes.replace(class_, '');
		this.className = newstr;
	}
	else {
		this.className += ' ' + class_;
	}
}

function mainDelegation(event) {
	var target, parentClass;
	target = event['target'];
	parentClass = target.parentNode.className;
	if (parentClass === 'fta_size' || parentClass === 'fta_color') {
		return;
	}
	var patternMapping = {
		fta_bold: '[b]%1[/b]',
		fta_italic: '[i]%1[/i]',
		fta_lt: '[lt]%1[/lt]',
		fta_underline: '[u]%1[/u]',
		fta_center: '[center]%1[/center]',
		fta_link: '[a=%1]%2[/a]',
		fta_img: '[img]%1[/img]',
		fta_video: '[video]%1[/video]',
		size_dropdown_ul: '[size=%2]%1[/size]',
		color_dropdown_ul: '[color=%2]%1[/color]',
		fta_quote: '[q]%1[/q]',
		fta_spoiler: '[spoiler]%1[/spoiler]',
	};
	if (patternMapping.hasOwnProperty(parentClass)) {
		var dropdowns, urlgetters, input, start, end, firstReplace,
		 secondReplace, replaceList, newSubstring, inputValue, newString, caretPos;
		dropdowns = {
		'color_dropdown_ul': getColor,
		'size_dropdown_ul': getSize,
	    };
	    urlgetters = {
		'fta_link': getLink,
		'fta_img': getImage,
		'fta_video': getVideo,
	    };
	    input = this.nextElementSibling;
	    start = input.selectionStart;
	    end = input.selectionEnd;
	    inputValue = input.value;
	    if (start === end) {
	    	firstReplace = ''
	    }
	    else {
	    	firstReplace = inputValue.substring(start, end);
	    }

	    if (dropdowns.hasOwnProperty(parentClass)) {
	    	secondReplace = dropdowns[parentClass](target);
	    }
	    else if (urlgetters.hasOwnProperty(parentClass)) {
	    	replaceList = urlgetters[parentClass](firstReplace);
	    	firstReplace = replaceList[0];
	    	if (!(firstReplace)) {
	    		return;
	    	}
	    	secondReplace = replaceList[1];
	    }
	    else {
	    	secondReplace = '';
	    }
        newSubstring = patternMapping[parentClass];
        newSubstring = newSubstring.replace('%1', firstReplace).replace('%2', secondReplace);
        if (firstReplace) {
        	caretPos = start + newSubstring.length;
        }
        else {
        	caretPos = start + (newSubstring.indexOf(']') + 1);
        }
        newString = inputValue.substring(0, start)+newSubstring+inputValue.substring(end, inputValue.length);
        input.value = newString;
        input.focus();
        input.setSelectionRange(caretPos, caretPos);
	}  
	else {
		return;
	}
}

function getSize(target) {
    var sizeMap = {
	            	'Very small': '10',
	            	'Small': '14',
	            	'Medium': '18',
	            	'Large': '26',
	            	'Very large': '36'
	};
	return sizeMap[target.innerHTML];
}
function getColor(target) {
	return target.innerHTML.toLowerCase();
}	
function getVideo(value) {
	if (!(value)) {
		value = prompt('Add Video', 'Please enter a link to a video file.');
	}
	return [value, ''];
}
function getImage(value) {
	if (!(value)) {
		value = prompt('Add Image', 'Please enter a link to an image.');
	}
	return [value, ''];
}
function getLink(value) {
	if (!(value)) {
		value = prompt('Link', 'Please enter a link.');
	}
	return [value, 'Some name'];
}

function generateLi() {
 var ulists = document.getElementsByClassName('fta_button_row');
 liClassesTitles = [
 ['bold', 'Bold'], ['italic', 'Italic'], ['lt', 'Line through'],
 ['underline', 'Underline'], ['center', 'Centered'], ['link', 'Hyperlink'],
 ['img', 'Image'], ['video', 'Video'], ['size', 'Size'], ['color', 'Color'],
 ['quote', 'Quote'], ['spoiler', 'Spoiler']
 ];
 for (var j = 0; j < ulists.length; j++) {
 var ul = ulists[j];
 pos = 0;
 liClassesTitles.forEach(function(sublist, ind) {
 var li = document.createElement('LI');
 li.className = 'fta_' + sublist[0];
 li.title = sublist[1];
 ul.appendChild(li);
 var span = document.createElement('span');
 span.style.backgroundPosition = pos.toString() + 'px 0px';
 pos -= 30;
 li.appendChild(span);
 if (sublist[0] === 'size') {
 var div = document.createElement('DIV');
 div.className = 'size_dropdown hidden';
 li.appendChild(div);
 var sizeUl = document.createElement('UL');
 sizeUl.className = 'size_dropdown_ul';
 div.appendChild(sizeUl);
 valuesList = ['Very small', 'Small', 'Medium', 'Large', 'Very large'];
 valuesList.forEach(function(text) {
 var li = document.createElement('LI');
 var node = document.createTextNode(text);
 li.appendChild(node);
 sizeUl.appendChild(li);
 });
 }
 else if (sublist[0] === 'color') {
 var div = document.createElement('DIV');
 div.className = 'color_dropdown hidden';
 li.appendChild(div);
 var sizeUl = document.createElement('UL');
 sizeUl.className = 'color_dropdown_ul';
 div.appendChild(sizeUl);
 valuesList = ['Red', 'Green', 'Blue', 'White', 'Orange', 'Purple', 'Black'];
 valuesList.forEach(function(text) {
 var li = document.createElement('LI');
 var node = document.createTextNode(text);
 li.appendChild(node);
 sizeUl.appendChild(li);
 });
 }
 });
 }
 }
document.addEventListener('DOMContentLoaded', tryIt);

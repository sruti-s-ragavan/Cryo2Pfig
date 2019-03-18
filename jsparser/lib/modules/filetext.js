define(['underscore', 'jquery'], function() { 
	var fileContents = function(n, doneCallback){
		var xhr;
		var text;
		if (window.XMLHttpRequest) {
			xhr = new XMLHttpRequest();
		} else if (window.ActiveXObject) {
			xhr = new ActiveXObject("Microsoft.XMLHTTP");
		}
		xhr.onreadystatechange = handleStateChange;
		xhr.open("GET",n, true); 
		xhr.send();

		function handleStateChange(){
			if (xhr.readyState === 4){
				doneCallback(xhr.status == 200 ? xhr.responseText : null);
			}
		}
	}
	return {
		fileContents: fileContents
	};
});
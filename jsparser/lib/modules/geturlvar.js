define([],function(){

	var urlID = function (n, doneCallback) {
		var SearchString = n;
		var VariableArray = SearchString.split('&');
		for(var i = 0; i < VariableArray.length; i++){
			var KeyValuePair = VariableArray[i].split('=');
			if(KeyValuePair[0] == 'fn'){
				doneCallback(KeyValuePair[1]);
			}
		}
	}
	return{
		urlID: urlID
	};
});
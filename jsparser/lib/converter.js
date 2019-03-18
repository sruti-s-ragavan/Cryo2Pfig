// Code to find and record information about function definitions and invocations in JavaScript files

var PARENTHESIS = '(';
var BRACE = '{';

var parser = require('./lib/parser.js');
var fs = require('fs');

var functionStats = [];
var invocationStats = [];
var docLineList = [];

function readFile(fileName) {
	return fs.readFileSync(fileName, "utf8");
}

// removes delimiters
function cleanString(string) {
	string = string.replace(/\r/g, '');
	string = string.replace(/\t/g, '');
	string = string.replace(/\n/g, '');
	return string;
}

/* converts the contents of JavaScript file 
to an array of tokens, where each token is a variable name, 
literal, symbol, punctuation, etc. */
function generateTokenArray(contents) {
    
    var tokenArray = [];
    var tokenFunc = parser.tokenizer(contents);
    var token = tokenFunc(false);
    tokenArray.push(token);
    
    while (token.type != 'eof') {
        token = tokenFunc(false);
        tokenArray.push(token);
    }
    
    //console.log(tokenArray);
    return tokenArray;
}

function checkForLoop(token_array){
 for(token in token_array){
	if(token == JS_FOR){
		
	}
}
function checkPatterns(token_array){
	checkForLoop(token_array);
}
function getLineLengths(path, tokenArray) {
	var lineNumber, startPosition, endPosition, lineLength;
	var tokenIndex = 0;
	var list = {};
	var len_list = [];

	while (tokenIndex < (tokenArray.length - 1)) {
		lineNumber = tokenArray[tokenIndex].line;
		startPosition = tokenArray[tokenIndex].pos;
		
		// Move through all the tokens on a line
		while (tokenArray[tokenIndex].line == lineNumber && tokenIndex < (tokenArray.length - 1)) {
			tokenIndex++;
		}
		
		endPosition = tokenArray[tokenIndex - 1].pos;
		lineLength = (endPosition - startPosition) + 1;
		
		len_list.push(lineLength);
	}
	
	list["file"] = path;
	list["len"] = len_list;
	return list;
	
	
}

function checkContent(filePath, tokenArray, currentPosition, symbol, header) {
    
    var lastOpen, punctuation;
    var stack = [];
    var matching = { '(' : ')', '{' : '}', '[' : ']' };
    var closing = ")}]";
    var startingPosition = currentPosition;
    
    // check that the first token is the token expected/required
    if (tokenArray[currentPosition].value != symbol) {
        return 0;
    }
    
    while (tokenArray[currentPosition].type != 'eof') {
        // add opening punctuation to stack
        if (tokenArray[currentPosition].value in matching) {
            stack.push(tokenArray[currentPosition].value);
        }
        // check if token is closing punctuation
        punctuation = closing.indexOf(tokenArray[currentPosition].value);
        if (punctuation != -1) {
            // if token is closing punctuation, pop most recent opening punctuation from stack
            lastOpen = stack.pop();
            // compare most recent opening punctuation to closing punctuation
            if (matching[lastOpen] != closing[punctuation]) {
                // if opening and closing do not match (example: '{]') return 0 (false)
                return 0;
            }
            if (stack.length == 0) {
            	// the stack is empty after iterating over entire set of parameters '()' or function body '{}'
                // return the length of the parameters or function body (including opening and closing punc)
                return ((currentPosition - startingPosition) + 1);
            }
        }
        
        // check for nested functions
        if (tokenArray[currentPosition].value == 'function') {
        	functionIdentifier(filePath, contents, tokenArray, currentPosition, header);
        }
        
        // move to next token
        currentPosition += 1;
    }
}

function getFuncStats(filePath, fileContents, tokenArray, startFunc, header, endFunc, name) {
    //Note: In the case of a function call, the end of the call is the end of the header (i.e endHeaderPos = endFuncPos)
    
    var start = tokenArray[startFunc].pos;
    var end = tokenArray[endFunc].pos;
    var length = end - start;
    var functionContents = fileContents.slice(tokenArray[startFunc].pos, (tokenArray[endFunc - 1].pos) + 1);
    return {"src":path, "name": name, "start":start, "end":end, "length":length, "contents":functionContents, "header":header, "filepath":filePath};
}

function functionIdentifier(filePath, contents, tokenArray, currentPosition, header) {
    
    while (tokenArray[currentPosition].type != 'eof') {
    
    	var name;
    	var previousPath = "";
    	var originalPosition = currentPosition;
    	var isVariable = false;
    	
    	//If the function is stored in a variable, the variable name acts as the function name
    	//So this conditional looks for 'var identifier = ' to determine if the function definition that follows requires a name.
    	//Example: var adder = function(a, b, c) {...} vs. function adder(a,b,c) {...}
    	if (tokenArray[currentPosition].value == 'var') {
        	currentPosition += 1;
        	if (tokenArray[currentPosition].type == 'name') {
        		name = tokenArray[currentPosition].value;
            	currentPosition += 1;
            	if (tokenArray[currentPosition].value == '=') {
                	currentPosition += 1;
                	isVariable = true;
        		} else {
        			currentPosition += 1;
            		continue;
            	}
        	} else {
        		currentPosition += 1;
        		continue;
        	}
   	 	}
              
    	if (tokenArray[currentPosition].value == 'function') {
        	currentPosition += 1;
        	if (tokenArray[currentPosition].type == 'name' || isVariable == true) {
        		if (tokenArray[currentPosition].type == 'name') {
        			name = tokenArray[currentPosition].value;
        	    	currentPosition += 1;
        		}
        		
            	// checkContent ensures that opening and closing parenthesis are included at the end of the header
            	// checkContent will iterate over and count parameters or whitespace between parenthesis
            	var parameters = checkContent(filePath, tokenArray, currentPosition, PARENTHESIS, header);
            	if (parameters) {
            		// move to end of parameters / end of function header
                	currentPosition += parameters;
                	header += contents.slice(tokenArray[originalPosition].pos, tokenArray[currentPosition].pos);
                	
                	// add function header to file path
                	previousPath = filePath;
                	filePath += "/" + header;
                	
            	} else {
            		currentPosition += 1;
                	continue;
            	}
            	
				// checkContent ensures opening and closing curly braces at beginning and end of function definition
				// checkContent will iterate over and count tokens in function body
            	var functionBody = checkContent(filePath, tokenArray, currentPosition, BRACE, header);
            	if (functionBody) {
            		// move to the end of function body
               		currentPosition += functionBody;
            	} else {
            		currentPosition += 1;
                	continue;
            	}
                
        	} else {
        		currentPosition += 1;
            	continue;
        	}
    	} else {
    		currentPosition += 1;
        	continue;
    	}
    	
    	functionStats.push(getFuncStats(previousPath, contents, tokenArray, originalPosition, header, currentPosition, name));
    	header = "";
    	filePath = path;
    	previousPath = "";
    } 
}

// Determine if function being called has been previously defined
function findInvSource(invName) {
    var i;
    for (i = 0; i < functionStats.length; i++) {
    	if (functionStats[i].name == invName) {
    		return functionStats[i].header;
    	}
    }
    
    return "JavaScript_standard;.";
}

// Determine if function is contained in another function
function nestedCall(callStart, callEnd, invsrc) {
	var funcIndex;
	for (funcIndex = 0; funcIndex < functionStats.length; funcIndex++) {
		if ((functionStats[funcIndex].start < callStart) && (functionStats[funcIndex].end > callEnd)) {
			invsrc = invsrc + ";." + functionStats[funcIndex].header;
			return invsrc;
		}
	}
	
	return invsrc;
}

function getInvStats(filePath, fileContents, tokenArray, startFunc, header, endFunc, name) {
    //Note: In the case of a function call, the end of the call is the end of the header (i.e endHeaderPos = endFuncPos)
	
    var start = tokenArray[startFunc].pos;
    var end = tokenArray[endFunc].pos;
    var length = end - start;
    var functionContents = fileContents.slice(tokenArray[startFunc].pos, (tokenArray[endFunc - 1].pos) + 1);
    
    var invsrc = filePath;
    invsrc = nestedCall(start, end, invsrc);

    return {"src":filePath, "invsrc": invsrc, "name": name, "start":start, "end":end, "length":length, "contents":functionContents, "header":header, "filepath":filePath};
}

function invocationIdentifier(filePath, contents, tokenArray, currentPosition) {
    
    var originalPosition, name;
    
    while (tokenArray[currentPosition].type != 'eof') {
    
    	// look for 'myFunction()' but exclude 'var myFunction()' and 'function myFunction()'
        if (tokenArray[currentPosition].type == 'name' && tokenArray[currentPosition-1].type != 'keyword') {
        	name = tokenArray[currentPosition].value;
        	originalPosition = currentPosition;
            currentPosition += 1;
            
            // iterate over arguments and whitespace between parenthesis
            var parameters = checkContent(filePath, tokenArray, currentPosition, PARENTHESIS, "");
            if (parameters) {
                currentPosition += parameters;
                
                if (tokenArray[currentPosition].value == ';') {
                    var header = contents.slice(tokenArray[originalPosition].pos, tokenArray[currentPosition].pos);
                    invocationStats.push(getInvStats(filePath, contents, tokenArray, originalPosition, header, currentPosition, name));
            	} else {
            		currentPosition += 1;
                	continue;
                }
            } else {
            	currentPosition += 1;
            	continue;
            }
        } else {
        	currentPosition += 1;
        	continue;
        }
    }  
}

var files = process.argv.slice(2);
var fileNum;
var full_stats =[];

for (fileNum = 0; fileNum < files.length; fileNum++) {
	var path = files[fileNum];
	var readIn = readFile(path);
	
	// Calculate line lengths with delimiters
	var tokenArray = generateTokenArray(readIn);
	docLineList = (getLineLengths(path, tokenArray));
	
	
	// Remove delimiters to log file contents
	var contents = cleanString(readIn);
	tokenArray = generateTokenArray(contents);

	functionIdentifier(path, contents, tokenArray, 0, "");
	invocationIdentifier(path, contents, tokenArray, 0);

	var stats = {};
	//docLineList = JSON.stringify(docLineList);	
	//functionStats = JSON.stringify(functionStats);
	//invocationStats = JSON.stringify(invocationStats);
	
	stats["functions"] = functionStats;
	stats["invocations"] = invocationStats;
	stats["lengths"] = docLineList;	
	//stats = JSON.stringify(stats);
	full_stats.push(stats)	
	//console.log(stats);
}
console.log(JSON.stringify(full_stats));

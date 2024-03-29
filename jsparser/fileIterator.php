<?php
require 'lib/jparser-1-0-0/jparser-libs/jtokenizer.php';
error_reporting(0);
set_time_limit (0);
ini_set('memory_limit','128M');
ini_set("auto_detect_line_endings", true);

$JAVASCRIPT_STD = "JS_Std_lib";

function token_is_non_processed($token){
	 return( $token[0] == J_COMMENT || token_is_white_space($token));
}

function token_is_white_space($token){
	 return($token[0] == J_WHITESPACE || $token[0] == J_LINE_TERMINATOR );
}

function find_tokens_on_line($tokens, $line_number){
	$x = 0;
	$token_count = 0;
	while($tokens[$x][2] < $line_number)
		$x++;
	while($tokens[$x][2] == $line_number){
		if (!token_is_white_space($tokens[$x])){
			$token_count++;
		}
		$x++;
	}

	return $token_count;
}	

function fix_comment_line_error($tokens, $j){
	$comment_only_lines_count = 0;

	// in a token; [0]: token type, [1]: content string, [2]: line [3]: column / char in line.
	for($x = 0;$x<$j;$x++){
		if($tokens[$x][0] == J_COMMENT && substr($tokens[$x][1], 0,2) == "//"){
			$num_tokens_on_line = find_tokens_on_line($tokens, $tokens[$x][2]);
			if($num_tokens_on_line == 1){
				$comment_only_lines_count++;
			}
		}
	}
	
	return $comment_only_lines_count;
}
//TODO: make this return inclusively
//REMINDER: there is an incrementation later in the code that makes this inclusive. delete it.
//returns the length of a variable declaration, non-inclusive
function variable_length($token_num, $tokens){
	$token_num;
	$i;
	$num_braces = 0;
	for($i=$token_num+1;$i<count($tokens);$i++){
		if($tokens[$i][0] == ';'){
			break;
		}
	}
	return sum_to_token($tokens , $i) - sum_to_token($tokens,$token_num);
}
//TODO: make this return inclusively
//REMINDER: there is an incrementation later in the code that makes this inclusive. delete it.
//returns the length of a function invocation, non-inclusive
function invocation_length($token_num, $tokens){
	$token_num;
	$i;
	$num_braces = 0;
	for($i=$token_num+1;$i<count($tokens);$i++){
		if($tokens[$i][0] == '('){
			$num_braces +=1;
		}
		if($tokens[$i][0] == ')'){
			$num_braces -=1;
			if($num_braces ==0){
				break;
			}
		}
	}
	return sum_to_token($tokens, $i) - sum_to_token($tokens,$token_num);
}


function function_length($token_num, $tokens){
	$token_num;
	$i;
	$num_braces = 0;
	for($i=$token_num+1;$i<count($tokens);$i++){
		if($tokens[$i][0] == '{'){
			$num_braces +=1;
		}
		if($tokens[$i][0] == '}'){
			$num_braces -=1;
			if($num_braces ==0){
				break;
			}
		}
	}
	return sum_to_token($tokens , $i) - sum_to_token($tokens,$token_num);
}

function sum_to_token($tokens,$index){
	//print_r($token);
	$sum = 0;
	for($x = 0;$x<$index;$x++){
		$sum+=strlen($tokens[$x][1]);
	}
	return $sum;
}

function file_array($directory){

	$file_array = array();
	foreach (new RecursiveIteratorIterator(new RecursiveDirectoryIterator($directory)) as $filename)
	{
		if(strpos($filename, 'timbre.js') !== false){
			continue;
		}
		if(substr($filename, -3) == ".js" && strpos($filename,'JQuery.js')==FALSE && (strpos($filename,'vendor') == false) ){
			$file_array[] = $filename->getPathname();
		}

	}	
	return $file_array;
	
}

function get_tokens($source){
	
	$tokens = j_token_get_all( $source );
	return $tokens;
}

function variable_identifier($source, $fstring){
	$code = file_get_contents($source);
	$tokens = get_tokens($code);
	$source = ''.$source;
	$source = substr($source, strlen($fstring));
	for($i=0;$i<count($tokens);$i++){
		$j = $i+1;
		if($tokens[$i][0] == 3){
			while(1){
				//if the token type is not a comment, whitespace, or line terminator, then
				if(!token_is_non_processed($tokens[$j])){
					//it needs to be an identifier
					if($tokens[$j][0] !== J_IDENTIFIER){
						//if it's not, we need to continue on our token list
						break;
					}
					//otherwise, check if it's a function.
					// $token[$j][1] = name_of variable
					else{
						$num_equals = 0;
						$k = $j+1;	
						while(1){
							//perform the comment, whitespace, or line terminator check again
							if(!token_is_non_processed($tokens[$k])){
								// check for equals var funcName =
								if($tokens[$k][0] == '=' && $num_equals>=1){
									break 2;
								}else if($tokens[$k][0] == '=' && $num_equals<1){
									$num_equals++;
									//to next token
									$k++;
									continue;
								}

								//this checks if it's an uninitialized variable.
								if($tokens[$k][1] == ';'){
									$sum = sum_to_token($tokens,$i);
									$length = variable_length($i,$tokens);
									$var_start = sum_to_token($tokens,$j);
									$length +=1;
									$end = $sum + $length;
									$substring = 'UNINITIALIZED';
									$var_length = variable_length($i, $tokens);
									$var_length +=1;
									$var_header = $var_header = $tokens[$j][1];
									//generate variable entry for variable array.
									global $src_arg;
									$variable_stats[] = array("src" =>$src_arg.$source, "start" =>$sum, "length" => $length, "end" => $end, "contents" => $substring, "header" =>$var_header, "filepath" => ''. $source);
									//echo "<b>". $tokens[$j][1]."</b> <br>Start: $sum<br>Length: $length<br>End: $end <br>Contents: $substring <br>Var Header: $var_header<br><br>";
									break 2;
								}
								if($tokens[$k][0] != '=' && $num_equals<1){
									break 2;
								}
								if($tokens[$k][0] !== J_FUNCTION){
									//if it's not a function, then it's a variable
									$sum = sum_to_token($tokens,$i);
									$length = variable_length($i,$tokens);
									$var_start = sum_to_token($tokens,$j);
									$length +=1;
									$end = $sum + $length;
									$substring;
									$l = $k;
									while(1){
									//perform the comment, whitespace, or line terminator check again
										if($tokens[$l][1] == ';'){
											break;
										}
										else if(!token_is_non_processed($tokens[$l])){
											$substring = $substring . $tokens[$l][1];
											$l++;
										}else{
											$l++;
										}
									}
									$var_length = variable_length($i, $tokens);
									$var_length +=1;
									$var_header = $tokens[$j][1];
									//generate variable entry for variable array.
									global $src_arg;
									$variable_stats[] = array("src" => $src_arg.$source, "start" =>$sum, "length" => $length, "end" => $end, "contents" => $substring, "header" => $var_header, "filepath" => ''. $source);
									//echo "<b>". $tokens[$j][1]."</b> <br>Start: $sum<br>Length: $length<br>End: $end <br>Contents: $substring <br>Var Header: $var_header<br><br>";
									break 2;
								}else{ 
									break 2;
								}
							}else{
								$k++;
							}
						}	
					}
				} else{
					$j++;
				}
			}
		}
	}
	return $variable_stats;
}
function invocation_identifier($source,$file_array, $fstring){
	$tID = -1;
	
	$code = file_get_contents($source);
	//echo $source;
	$tokens = get_tokens($code);

	$invocation_stats = array();
	$source = ''.$source;
	$source = substr($source, strlen($fstring));
	
	for($i=0;$i<count($tokens);$i++){
		$j = $i+1;
		if($tokens[$i][0] == J_IDENTIFIER){
			while(1){
				//if the token type is not a comment, whitespace, or line terminator, then
				if(!token_is_non_processed($tokens[$j])){
					if($tokens[$j][0] == '('){
						//check if this is the start of a function.
						if($tID !== -1){
							if($tokens[$tID][0] == J_FUNCTION){
								$tID = -1;
								break 1;
							}
							$tID = -1;
						}
						//if it's an open paren, we can tell that this is a call.
						$sum = sum_to_token($tokens, $i);

						$length = invocation_length($i,$tokens);
						$length +=1;
						$end = $sum + $length;
						$call_header = substr($code, sum_to_token($tokens,$i), $length);

						$line_by_line = explode("\n", $code);
						//print_r($line_by_line);
						$comment_adjustment = fix_comment_line_error($tokens, $j);
						
						// var_dump($line_by_line);
						// echo "Line number".$tokens[$i][2];
						// echo "Comment lines".$comment_adjustment;
						
						//the -1 is for 0-indexing to fix an off-by-one error
						$substring = $line_by_line[$tokens[$i][2]-1];
						
						//get the name of the function call
						$pos = strpos($call_header, "(");
						$invocation_name = substr($call_header, 0, $pos);

						$inv_path = get_invocation_full_path($invocation_name,$file_array,$source);

						global $src_arg;
						$invocation_stats[] = array("src" => $src_arg.$source, "start" =>$sum, 
							"length" => $length, "end" => $end, "contents" => $substring, 
							"header" => $call_header, "filepath" => "".$source , 
							"invsrc" => $inv_path);

						//echo "<b>" . $tokens[$i][1]."</b> <br>Start: $sum<br>Length: $length<br> End: $end <br>Contents: $substring <br>Invocation header = $inv_path<br>";
						
						break;
					}else{									
						break;
					}
				}
				else{
					$prev = $j;
					$j++;
				}
			}
		}
	if(!token_is_non_processed($tokens[$i])){
			$tID = $i;
		}
	}
	
	return $invocation_stats;
}

function function_identifier($sourcefile, $folderPath){
	$source = ''.$sourcefile;
	$source = substr($source, strlen($folderPath));
	$code = file_get_contents($sourcefile);
	$function_stats = identify_functions($code, $source);
	return $function_stats;
}

function extract_function_body($func_contents){
	// look for position of first { and last } and rip out what's in between and call it the function body.
	$start_pos = strpos($func_contents, "{");
	$end_pos = strrpos($func_contents, "}");
	$length = strlen($func_contents);

	$func_body = substr($func_contents, $start_pos, $length-$start_pos);

	// echo $func_contents."\n";
	// echo "\n".$start_pos." ".$end_pos." ".strlen($func_contents)."\n";
	// echo $func_body."\n";
	return $func_body;
}

function gather_functions_if_class($func_header, $func_contents, $source){
	//Look through functions inside classes and collect them as well.
	//Assumption: if function name starts with an upper case character, it is a class. 
	//This is not a language rule, but rather a JS convention.
	//Otherwise, we can get into the nested function rabbit hole very easily.

	$start_char = $func_header[0];
	if($start_char>='A' && $start_char<='Z'){
		//function contents includes function header as well, and this leads to an infinite loop.
		$func_body = extract_function_body($func_contents);
		identify_functions($func_body, $source);
	}
}

function extract_header($header_line){
	//header format : 
	//var func = function(a)
	//this.multiply=function(a,b)
	
	$LHS_REGEX_PATTERN = "/(.*)\s*=\s*function(.*)/";
	preg_match($LHS_REGEX_PATTERN, $header_line, $matches);
	$lhs = $matches[1];

	$FUNCTION_IDENTIFIER_REGEX = "/.*(\.|\s)([a-z|A-Z]+)/";
	preg_match($FUNCTION_IDENTIFIER_REGEX, $lhs, $matches);
	$function_name = $matches[2];	
	return $function_name."()";
}

function identify_functions($code, $source){
    $tokens = get_tokens($code);
	    //echo "passed tokens";
    $function_stats = array();
    //list functions of type var fName = function(){}, and in a separate array, all variable declarations.
    for($i=0;$i<count($tokens);$i++){
        $j = $i+1;
        if($tokens[$i][0] == J_VAR || $tokens[$i][0] == J_THIS){ 
            while(1){
            	//if the token type is not a comment, whitespace, or line terminator, then
                if(!token_is_non_processed($tokens[$j]) && $tokens[$j][0] != '.'){
                    //it needs to be an identifier
                    if($tokens[$j][0] !== J_IDENTIFIER){
                        //if it's not, we need to continue on our token list
                        break;
                    }
                    //otherwise, check if it's a function.
                    else{
                    	$num_equals = 0;
                        //move on to next token
                        $k = $j+1;
                        while(1){
                            //perform the comment, whitespace, or line terminator check again
                            if(!token_is_non_processed($tokens[$k])){
                                // check for equals var funcName =
                                if($tokens[$k][0] == '=' && $num_equals>=1){
                                    break 2;
                                }else if($tokens[$k][0] == '=' && $num_equals<1){
                                    $num_equals++;
                                    //to next token
                                    $k++;
                                    continue;
                                }
                                // match var funcName = function
                                if($tokens[$k][0] !== J_FUNCTION){
                                    break 2;
                                }else{
                                	
                                	$sum = sum_to_token($tokens,$i);
                                    $length = function_length($i,$tokens);
                                    $function_start = sum_to_token($tokens,$j);

                                    $length +=1;
                                    $end = $sum + $length;
                                    $function_contents = substr($code, $sum, $length +1);
                                    $function_call_length = invocation_length($i, $tokens);
                                    $function_call_length +=1;
                                    $function_header_line = substr($code, sum_to_token($tokens,$i), $function_call_length);
                                    $function_header = extract_header($function_header_line);
                                    //generate function entry for function array.
                                    global $src_arg;
                                    $function_stats[] = array("src" => $src_arg.$source, "start" =>$sum, 
                                    	"length" => $length, "end" => $end, "contents" => $function_contents, 
                                    	"header" => $function_header, "filepath" => "");
                                    //echo "<b>". $tokens[$j][1]."</b> <br>Start: $sum<br>Length: $length<br>End: $end <br>Contents: $function_contents <br>Function Header: $function_header<br>Source File: $source<br><br>";
                                    gather_functions_if_class($function_header, $function_contents);
                                    break 2;
                                }
                            }else{
                                $k++;
                            }
                        }
                    }
                } else{
                    $j++;
                }
            }
        }
    }
    //get function of type function functionName(){}
    for($i=0;$i<count($tokens);$i++){
        $j = $i+1;
        //if token is a function
        if($tokens[$i][0] == J_FUNCTION){
            while(1){
                //if the token type is not a comment, whitespace, or line terminator, then
                if(!token_is_non_processed($tokens[$j])){
                    if($tokens[$j][0] != '('){
                        //if the token is an open paren, we can assume that this is a function declaration.
                        $sum = sum_to_token($tokens,$i);
                        $length = function_length($i,$tokens);
                        $function_start = sum_to_token($tokens,$j);

                        $length +=1;
                        $end = $sum + $length;
                        $function_call_length = invocation_length($j, $tokens) + 1;
                        $function_header = substr($code, sum_to_token($tokens,$j), $function_call_length);
                        $function_contents = substr($code, $sum, $length);
                        $function_nests[] = array(sum_to_token($tokens,$i), $end, $function_header);

                        $nested_within = array();
                        //generate function entry in function array
                        global $src_arg;

                        if (strcmp($source, "") === false){
                        	echo "Empty sourcce : ".$src_arg.$source." ".$function_header;
                        }
                        $function_stats[] = array("src" => $src_arg.$source, "start" =>$sum, 
                        	"length" => $length, "end" => $end, "contents" => $function_contents, 
                        	"header" => $function_header, "filepath" => "");
                        //echo "function header = $function_header <br>";
                        //echo "<b>". $tokens[$j][1]."</b> <br>Start: $sum<br>Length: $length<br> End: $end <br>Contents: $function_contents <br>Function header:$function_header!<br>Source File: $source<br><br>";
                        gather_functions_if_class($function_header, $function_contents);
                        break;
                    }else{
                        break;
                    }
                }
                else{
                    $j++;
                }
            }
        }
    }
    return $function_stats;
}

function array_filter_recursive($input){ 
	foreach ($input as &$value) { 
		if (is_array($value)){
			$value = array_filter_recursive($value); 
		} 
	} 
	return array_filter($input); 
} 
function get_invocation_full_path($invocation_name, $file_array, $invocation_file_path){
	//echo "<h1> fp = $invocation_file_path, name = $invocation_name</h1>";
	global $JAVASCRIPT_STD;

	foreach($file_array as $f){
		$func_list = $f["functions"];
		for($i=0;$i<count($func_list);$i++){

			$pos = strpos($func_list[$i]["header"], "(");
			$func_name = substr($func_list[$i]["header"], 0, $pos);

			if(strcmp($func_name, $invocation_name) == 0){
				// full path of where function is declared, starting with \/hexcom
				$src = $func_list[$i]["src"];
				// if nested, the nesting path relative to $declaration_file, else relative path of file (js_v9\/main.js)
				$filepath = $func_list[$i]["filepath"]; 
				//function_name()
				$header = $func_list[$i]["header"];

				$fully_qualified_path = "";

				if(strpos($src, $filepath) === false){
					$fully_qualified_path = $src.$filepath;
				}
				else{
					$fully_qualified_path = $src;
				}
				return $fully_qualified_path.";.".$header;
			}
		}
	}

	return $JAVASCRIPT_STD.";.".$invocation_name."()";

}
function get_file_functions_array($file_name_array, $fstring){
	
	$file_functions = array();
	$i = 0;
	foreach($file_name_array as $file){
			if($file == './src/hexcom/2014-05-18-20:34:05/js/timbre.js'){
				continue;
			}
			$function_sorted = function_identifier($file, $fstring);
			//echo "this is file $i<br>";
			//$x = memory_get_usage();
			//echo "<h1>Memory usage is $x</h1>";
			if($function_sorted !== NULL){
				usort($function_sorted,"custom_sort");
			}
			$file_functions[] = array("functions" => $function_sorted);
			
		$i++;
	}

	return $file_functions;
}

function get_file_invocations_array($file_array, $file_functions_array, $fstring){
	$file_invocations = array();
	foreach($file_array as $file){
		
		$invocation_sorted = invocation_identifier($file,$file_functions_array, $fstring);
		usort($invocation_sorted,"custom_sort");
		$file_invocations[] = array("invocations" => $invocation_sorted);
	}
	
	return $file_invocations;
}

function get_file_variables_array($file_name_array, $fstring){
	$file_variables = array();
	foreach($file_name_array as $file){
		$variables_sorted = variable_identifier($file, $fstring);
		usort($variables_sorted,"custom_sort");
		$file_variables[] = array("variables" => $variables_sorted);
	}
	return $file_variables;
}

function pretty_print_file_array($file_array){
		echo "<pre>"; 
		print_r($file_array);
		echo "</pre>";
}

function custom_sort($a,$b) {
    return $a["start"]>$b["start"];
}

function nested_variables($file_array){
	foreach($file_array as &$f){
		$func_list = $f["functions"];
		$var_list = $f["variables"];
		// $c = count($var_list);
		// $fc = count($func_list);
		// echo "var count = $c, func count = $fc";
		for($i=0;$i<count($var_list);$i++){
			for($j=0;$j<count($func_list);$j++){
				//compare the function at $j with the invocation at $i
				//echo "var start, end = " . $var_list[$i]["start"]. "," .$var_list[$i]["end"] . ", Function start, end = " . $func_list[$j]["start"] . ",". $func_list[$j]["end"] .  "<br>";
				if($var_list[$i]["start"]>$func_list[$j]["start"]&&$var_list[$i]["end"]<$func_list[$j]["end"] ){
					
					$var_list[$i]["filepath"] .= "/" . $func_list[$j]["header"];
					$f["variables"] =$var_list;
				}
			}
		}
	}
	return $file_array;
}

function compare_by_start_offset($a, $b){
	if($a["start"] == $b["start"]){
		return 0;
	}
	return $a["start"] > $b["start"] ? 1 : -1;
}

function nested_invocations($file_array){
	foreach($file_array as &$f){
		$func_list = $f["functions"];
		$invoc_list = $f["invocations"];
		// $c = count($invoc_list);
		// $fc = count($func_list);
		// echo "var count = $c, func count = $fc";
		for($i=0;$i<count($invoc_list);$i++){
			$nesting_list = [];
			for($j=0;$j<count($func_list);$j++){
				//compare the function at $j with the invocation at $i
				//echo "invocation start, end = " . $invoc_list[$i]["start"]. "," .$invoc_list[$i]["end"] . ", Function start, end = " . $func_list[$j]["start"] . ",". $func_list[$j]["end"] .  "<br>";
				if($invoc_list[$i]["start"]> $func_list[$j]["start"]&&
					$invoc_list[$i]["end"]< $func_list[$j]["end"] ){
					array_push($nesting_list, $func_list[$j]);
				}
			}
			usort($nesting_list, "compare_by_start_offset");
			$nesting_levels = count($nesting_list);

			$filepath = "";
			for($k=0; $k<$nesting_levels-1; $k++){
				$filepath = $filepath."/".$nesting_list[$k]["header"];
			}
			$invoc_list[$i]["filepath"] = $filepath;
			$invoc_list[$i]["header"] = $nesting_list[$nesting_levels-1]["header"];
			$f["invocations"] = $invoc_list;
		}
	}
	return $file_array;
}

function nested_functions($file_array){
	foreach($file_array as &$f){
		$func_list = $f["functions"];
		for($i=1;$i<count($func_list);$i++){
			$nesting_path = "";
			for($j=0;$j<$i;$j++){

				//compare the function at $j with the function at $i
				//print_r( $func_list[$i]);
				if($func_list[$i]["start"] > $func_list[$j]["start"] 
					and $func_list[$i]["end"]<$func_list[$j]["end"]){
					$nesting_path = $nesting_path. "/". $func_list[$j]["header"];
				}
			}
			//TODO: this could as might be made empty when there is no nesting, and then fix in other places
			if(strcmp("", $nesting_path) !== false){
				$func_list[$i]["filepath"] = $nesting_path;
			}
		}
		$f["functions"] = $func_list;
	}
	
	return $file_array;
}

function get_line_lengths($file_name_array, $n){
	
	$file_lengths = array();
	global $src_arg;
	foreach($file_name_array as $file){ 
		$fName = $file . "";
		//$file_lengths[] = $fName
		$handle = fopen($fName, "r");
		if ($handle) {
			$len = array();
			while (($line = fgets($handle)) !== false) {
				$len[] = strlen($line);
				// process the line read.
			}
			//echo("hell0");
			$file_lengths["lengths"][]=  array("file"=>$src_arg . substr($fName, strlen($n)) ,"len" =>$len);
		} else {
			echo("error");
		}
		
		fclose($handle);
	
	}
	return($file_lengths);
}

//merge three arrays of the same size.
function merge_arrays($one, $two, $key1, $key2){
	$merged_array= array();
	for($i=0;$i<count($one);$i++){
		$merged_array[] = array($key1 =>$one[$i][$key1],$key2 =>$two[$i][$key2]);
	}
	return $merged_array;
}

$file = $argv[1];
$src_arg = strstr($argv[1],'/hex');
$file_name_array = file_array($file);

/*
echo "<pre>";
print_r($file_name_array);
echo "</pre>";
*/

	
$vendor_pos = array();
$fna_minus_jq = array();
function is_not_vendor($s){
	if((strpos($s,'vendor') !== false) || (strpos($s,'jquery') !== false) ){
		return false;
	}
	else{
		return true;
	}
}
$file_name_array = array_filter($file_name_array, "is_not_vendor");
$file_functions_array = get_file_functions_array($file_name_array, $file);
$file_functions_array = nested_functions($file_functions_array);

$file_invocations_array = get_file_invocations_array($file_name_array, $file_functions_array,$file);

//$file_variables_array = get_file_variables_array($file_name_array,$file);
$array_merged = merge_arrays($file_functions_array, $file_invocations_array,"functions","invocations");

//$array_merged = nested_variables($array_merged);
$array_merged = nested_invocations($array_merged);
$array_merged[] = get_line_lengths($file_name_array, $file);

//pretty_print_file_array($array_merged);
echo json_encode($array_merged);
?> 

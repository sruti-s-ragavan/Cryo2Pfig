function add(a, b) {
    var sum = a + b;
    return sum;
}

function arrayUsages(){
	var arr = []
	arr.push(1)
	function something(){
		console.log("something")
	}
	something();
}
function main() {
    add(1, 2);
    console.log("called 'add(...)'");

    arrayUsages();
	}
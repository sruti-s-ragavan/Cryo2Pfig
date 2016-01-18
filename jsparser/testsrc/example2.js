function sayHi() {
    console.log("Hello, World!");
}

function sayBye() {
    console.log("Bye, World!");
}

function Class(){
	this.method = function(){
		sayHi();
	};
};

var klas = new Class();
klas.method();
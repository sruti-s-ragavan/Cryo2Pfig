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
	this.anotherMethod = function(){
		for(var i=0; i<10; i++){
			this.method();
		}
	}
};

function Printer(name){
	this.name = name;

	this.printHi = function(){
		console.log("Hi, ", this.name);
	}

	this.printBye = function(){
		console.log("Bye, ", this.name);
	}
}

function sayHi() {
    new Printer("James").printHi();
}

function sayBye() {
    new Printer("James").printBye();
}


function Class(){
	this.perItem = function(){
		sayHi();
	};
	this.process = function(){
		for(var i=0; i<10; i++){
			this.perItem();
		}
	}
	new Printer().printHi();
};


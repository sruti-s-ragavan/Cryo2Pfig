function search(twoD,oneD){
	for(var i=0;i<twoD.length;i++){
		if(twoD[i][0] == oneD[0] && twoD[i][1] == oneD[1]) {
			return true;
		}
	}
	return false;
}
function floodFill(clock,side,index,deleting) {
	if(clock.blocks[side] === undefined || clock.blocks[side][index] === undefined){return;}
	var color = clock.blocks[side][index].color;
	for(var x =-1;x<2;x++){
		for(var y =-1;y<2;y++){
			if(Math.abs(x)==Math.abs(y)){continue;}
			if(clock.blocks[(side+x+clock.sides)%clock.sides] === undefined){continue;}
			if(clock.blocks[(side+x+clock.sides)%clock.sides][index+y] !== undefined){
				if(clock.blocks[(side+x+clock.sides)%clock.sides][index+y].color == color && search(deleting,[(side+x+clock.sides)%clock.sides,index+y]) === false) {
					deleting.push([(side+x+clock.sides)%clock.sides,index+y]);
					floodFill(clock,(side+x+clock.sides)%clock.sides,index+y,deleting);
				}
			}
		}
	}
}
function consolidateBlocks(clock,side,index){
	var sidesChanged =[];
	var deleting=[];
	deleting.push([side,index]);
	
	floodFill(clock,side,index,deleting);
	var deleteList= deleting;
	if(deleteList.length<3){return;}
	var i;
	for(i in deleteList){
		var arr = deleteList[i];
		if(arr !== undefined && arr.length==2) {
			if(sidesChanged.indexOf(arr[0])==-1){
				sidesChanged.push(arr[0]);
			}
			clock.blocks[arr[0]][arr[1]].deleted = 1;
		}
	}
	
}

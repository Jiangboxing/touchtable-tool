const http = new XMLHttpRequest()

let intervalId = -1;
let fast = false;
let pause = true;
let controlled = 0;

startSim()

function toggleSim(event) {
    let playButton = document.getElementById('playButton')
    if (pause) {
		intervalId = 500;
        playButton.innerHTML = '&#10074;&#10074;';
		pause = false
		socket.emit('simPlay');
    } else {
        intervalId = -1;
        playButton.innerHTML = '&#9658;';
		pause = true
		socket.emit('simPause');
    }
    event.preventDefault();

    return false;
}

function toggleControl(event) {
    let smartButton = document.getElementById('smartButton')
    if (controlled == 0) {
        smartButton.style.backgroundColor='#FFFF88';
		controlled = 1
		socket.emit('controlOn');
    } else if (controlled == 1) {
        smartButton.style.backgroundColor='#88FF88';
		controlled = 2
		socket.emit('controlIsland');
    } else {
        smartButton.style.backgroundColor='#CCCCCC' ;
		controlled = 0
		socket.emit('controlOff');
    }
    return false;
}


function startSim(){
    intervalId = setInterval(() => {
		 doTick();
    }, 1000);
}

function isPaused() {
	return intervalId == -1;
}

function pauseSim() {
	let playButton = document.getElementById('playButton');
    intervalId = -1;
    playButton.innerHTML = '&#9658;';
	pause = true
	socket.emit('simPause');
}

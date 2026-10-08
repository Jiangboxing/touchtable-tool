const http = new XMLHttpRequest()

let intervalId = -1;
let fast = false;
let pause = true;
let controlled = 0;

//startSim()

function setSimulationButtonState(isRunning) {
	let playButton = document.getElementById('playButton');
	if (!playButton) {
		return;
	}

	if (isRunning) {
		intervalId = 500;
		playButton.innerHTML = '&#10074;&#10074;';
		pause = false;
	}
	else {
		intervalId = -1;
		playButton.innerHTML = '&#9658;';
		pause = true;
	}
}

function playSimulation(event) {
	setSimulationButtonState(true);
	socket.emit('simPlay');
	if (event) {
		event.preventDefault();
	}

	return false;
}

function pauseSimulation(event) {
	setSimulationButtonState(false);
	socket.emit('simPause');
	if (event) {
		event.preventDefault();
	}

	return false;
}

function toggleSim(event) {
	if (pause) {
		return playSimulation(event);
	}

	return pauseSimulation(event);
}

function ensureSimulationPlaying() {
	return playSimulation();
}

socket.on('connect', function() {
	if (!pause) {
		socket.emit('simPlay');
	}
});

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

/*
function startSim(){
    intervalId = setInterval(() => {
		 doTick();
    }, 1000);
}
*/

function isPaused() {
	return intervalId == -1;
}

/*
function pauseSim() {
	let playButton = document.getElementById('playButton');
    intervalId = -1;
    playButton.innerHTML = '&#9658;';
	pause = true
	socket.emit('simPause');
}
*/

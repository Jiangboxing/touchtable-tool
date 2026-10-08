const socket = io();
$(function () {
    socket.on('data', function(data){
        plotNetwork(data.network);
        console.log(data)
		isMaster = true;
        //document.getElementById('clock').innerHTML = new Date(DEMData.host.currentTime * 1000);
    })
});

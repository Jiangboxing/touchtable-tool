var express = require("express");
var app = express();
const bodyParser = require("body-parser");
var cors = require('cors');
var http = require('http').createServer(app);
var io = require('socket.io')(http);
const request = require('request');


app.use(bodyParser.urlencoded({ extended: true }));
app.use(bodyParser.json());

app.use(cors());
app.use(express.static('static'))

let DEMIp = process.env.DEM_HOST || 'localhost';
let DEMPort = process.env.DEM_PORT || '3001';
let url = 'http://' + DEMIp + ':' + DEMPort + '/'
let urlForTick = url + "tick";

console.log(urlForTick)

app.get('/', (req, res) => {
    res.sendFile(__dirname + '/static/index.html');
})

app.get('/graphs', (req, res) => {
  res.sendFile(__dirname + '/static/graphs.html');
})

app.post('/dem/state', (req, res) => {
    io.sockets.emit('data', req.body);
    res.sendStatus(202)
})

io.on('connection', function(socket){
    console.log('a user connected', socket.id);

    socket.on('requestTick', function() {
        //request(urlForTick, {json: {clientId: socket.id}}, (err, res, body) => {
        //    io.sockets.connected[socket.id].emit('tickResponse', body);
        //});
    });

	socket.on('simPlay', function() {
        request.get(url + 'syncset/host/pause/false', (err, res, body) => {
			if (err) {
                return console.log(err);
            }
		});
    });
	
	socket.on('simPause', function() {
		request.get(url + 'syncset/host/pause/true', (err, res, body) => {
			if (err) {
                return console.log(err);
            }
		});
    });
	
	socket.on('controlOn', function() {
        request.get(url + 'syncset/host/executeControl/true', (err, res, body) => {
			if (err) {
                return console.log(err);
            }
		});
		request.get(url + 'syncset/Auctioneer/islanding/false', (err, res, body) => {
			if (err) {
                return console.log(err);
            }
		});
    });
	
	socket.on('controlIsland', function() {
		request.get(url + 'syncset/host/executeControl/true', (err, res, body) => {
			if (err) {
                return console.log(err);
            }
		});
        request.get(url + 'syncset/Auctioneer/islanding/true', (err, res, body) => {
			if (err) {
                return console.log(err);
            }
		});
    });
	
	socket.on('controlOff', function() {
		request.get(url + 'syncset/host/executeControl/false', (err, res, body) => {
			if (err) {
                return console.log(err);
            }
		});
		request.get(url + 'syncset/Auctioneer/islanding/false', (err, res, body) => {
			if (err) {
                return console.log(err);
            }
		});
    });

    socket.on('requestTicks', function() {
       request(urlForTick, {json: {clientId: socket.id}}, (err, res, body) => {
            io.sockets.connected[socket.id].emit('tickResponse', body);
        });
    });

    socket.on('requestControl', function() {
		//io.sockets.connected[socket.id].emit('obtainedControl');
    });

	socket.on('removeDevice', function(name) {
		request.post(url + 'synccmds', {json: 
			[
				{ cmd: 'removeObj', entity : name},
				{ cmd: 'removeObj', entity : "Controller-"+name} 
			]
		}, (err, res, body) => {
				console.log(res.statusCode);
		});
		
	});

	socket.on('addDevice', function(settings) {
        let endpoint = settings.endpoint;
        let config = {
            name: endpoint[0].toUpperCase() + endpoint.slice(1) + '-' + settings.deviceId +
                '-House-' + settings.housenumber,
            smart: settings.isSmart,
			meter: 'SmartMeter-House-'+settings.housenumber,
			housenumber: settings.housenumber
        };

        switch (settings.endpoint) {
            case 'battery':
                addBattery(config);
                break;
            case 'solarPanel':
                addSolarPanel(config);
                break;
            case 'dishWasher':
                addDishwasher(config);
                break;
            case 'washingMachine':
                addWashingMachine(config);
                break;
            case 'vehicle':
                addVehicle(config);
                break;
            case 'heatpump':
                addHeatpump(config);
                break;
            default:

        }
	});

    socket.on('editDevice', function(settings) {
		request.post(url + 'syncsetnp/'+settings.name, {json: 
			settings.properties
		}, (err, res, body) => {
				console.log(res.statusCode);
		});
    });

    socket.on('fixCable', function(settings) {
        request.post(url + 'synccmds', {json: 
			[
				{ cmd: 'callFunction', entity : settings.name, func: 'reset', args: {'param': 'True'} }
			]
		}, (err, res, body) => {
				console.log(res.statusCode);
		});
    })
});

function addBattery(config) {
	request.post(url + 'synccmds', {json: 
		[
			{ cmd: 'createObj', 'entity' : 'BufDev', 'val': 
				[
					{name: config.name},
					{host: null}
				],
			},
			{ cmd: 'setVar', entity: config.name, 'var': 'capacity', 'val': 10000 },
			{ cmd: 'setVar', entity: config.name, 'var': 'initialSoC', 'val': 5000 },
			{ cmd: 'setVar', entity: config.name, 'var': 'chargingPowers', 'val': [-4000, 4000] },
			{ cmd: 'setVar', entity: config.name, 'var': 'timeBase', 'val': 900 },
			{ cmd: 'setVar', entity: config.name, 'var': 'strictComfort', 'val': false },
			{ cmd: 'callFunction', entity : config.name, func: 'startup', args: null},
			{ cmd: 'callFunction', entity : config.meter, func: 'addDevice', args: {obj: config.name}},
			{ cmd: 'setObj', entity: config.name, 'var': 'meter', 'val': config.meter },
			{ cmd: 'setVar', entity: config.name, 'var': 'balancing', 'val': true },
			{ cmd: 'createObj', 'entity' : 'BufAuctionCtrl', 'val': 
				[
					{name: "Controller-"+config.name},
					{obj: config.name},
					{obj: "Aggregator-"+config.housenumber},
					{host: null}
				],
			},
			{ cmd: 'setVar', entity: "Controller-"+config.name, 'var': 'strictComfort', 'val': false },
			{ cmd: 'callFunction', entity : "Controller-"+config.name, func: 'startup', args: null}
		]
	}, (err, res, body) => {
            console.log(res.statusCode);
    });
}

function addSolarPanel(config) {
	request.post(url + 'synccmds', {json: 
		[
			{ cmd: 'createObj', 'entity' : 'SolarPanelDev', 'val': 
				[
					{name: config.name},
					{host: null},
					{obj: 'Sun'}
				],
			},
			{ cmd: 'setVar', entity: config.name, 'var': 'size', 'val': 16 },
			{ cmd: 'setVar', entity: config.name, 'var': 'panels', 'val': 10 },
			{ cmd: 'setVar', entity: config.name, 'var': 'wattPeak', 'val': 300 },
			{ cmd: 'setVar', entity: config.name, 'var': 'timeBase', 'val': 900 },
			{ cmd: 'setVar', entity: config.name, 'var': 'strictComfort', 'val': false },
			{ cmd: 'callFunction', entity : config.name, func: 'startup', args: null},
			{ cmd: 'callFunction', entity : config.meter, func: 'addDevice', args: {obj: config.name}},
			{ cmd: 'createObj', 'entity' : 'CurtAuctionCtrl', 'val': 
				[
					{name: "Controller-"+config.name},
					{obj: config.name},
					{obj: "Aggregator-"+config.housenumber},
					{host: null}
				],
			},
			{ cmd: 'setVar', entity: "Controller-"+config.name, 'var': 'strictComfort', 'val': false },
			{ cmd: 'callFunction', entity : "Controller-"+config.name, func: 'startup', args: null}
		]
	}, (err, res, body) => {
            console.log(res.statusCode);
    });

}




function addWashingMachine(config) {
    request.post(url + 'synccmds', {json: 
		[
			{ cmd: 'createObj', 'entity' : 'TtTsDev', 'val': 
				[
					{name: config.name},
					{host: null},
				],
			},
			{ cmd: 'setVar', entity: config.name, 'var': 'strictComfort', 'val': false },
			{ cmd: 'callFunction', entity : config.name, func: 'startup', args: null},
			{ cmd: 'callFunction', entity : config.meter, func: 'addDevice', args: {obj: config.name}},
			{ cmd: 'createObj', 'entity' : 'TsAuctionCtrl', 'val': 
				[
					{name: "Controller-"+config.name},
					{obj: config.name},
					{obj: "Aggregator-"+config.housenumber},
					{host: null}
				],
			},
			{ cmd: 'setVar', entity: "Controller-"+config.name, 'var': 'strictComfort', 'val': false },
			{ cmd: 'callFunction', entity : "Controller-"+config.name, func: 'startup', args: null}
		]
	}, (err, res, body) => {
            console.log(res.statusCode);
    });
}

function addDishwasher(config) {
    request.post(url + 'synccmds', {json: 
		[
			{ cmd: 'createObj', 'entity' : 'TtTsDevDw', 'val': 
				[
					{name: config.name},
					{host: null},
				],
			},
			{ cmd: 'setVar', entity: config.name, 'var': 'strictComfort', 'val': false },
			{ cmd: 'callFunction', entity : config.name, func: 'startup', args: null},
			{ cmd: 'callFunction', entity : config.meter, func: 'addDevice', args: {obj: config.name}},
			{ cmd: 'createObj', 'entity' : 'TsAuctionCtrl', 'val': 
				[
					{name: "Controller-"+config.name},
					{obj: config.name},
					{obj: "Aggregator-"+config.housenumber},
					{host: null}
				],
			},
			{ cmd: 'setVar', entity: "Controller-"+config.name, 'var': 'strictComfort', 'val': false },
			{ cmd: 'callFunction', entity : "Controller-"+config.name, func: 'startup', args: null}
		]
	}, (err, res, body) => {
            console.log(res.statusCode);
    });
}

function addVehicle(config) {
    request.post(url + 'synccmds', {json: 
		[
			{ cmd: 'createObj', 'entity' : 'TtBtsDev', 'val': 
				[
					{name: config.name},
					{host: null},
				],
			},
			{ cmd: 'setVar', entity: config.name, 'var': 'strictComfort', 'val': false },
			{ cmd: 'setVar', entity: config.name, 'var': 'capacity', 'val': 50000 },
			{ cmd: 'setVar', entity: config.name, 'var': 'timeBase', 'val': 900 },
			{ cmd: 'setVar', entity: config.name, 'var': 'chargingPowers', 'val': [0, 7000] },
			{ cmd: 'callFunction', entity : config.name, func: 'startup', args: null},
			{ cmd: 'callFunction', entity : config.meter, func: 'addDevice', args: {obj: config.name}},
			{ cmd: 'createObj', 'entity' : 'BtsAuctionCtrl', 'val': 
				[
					{name: "Controller-"+config.name},
					{obj: config.name},
					{obj: "Aggregator-"+config.housenumber},
					{host: null}
				],
			},
			{ cmd: 'setVar', entity: "Controller-"+config.name, 'var': 'strictComfort', 'val': false },
			{ cmd: 'callFunction', entity : "Controller-"+config.name, func: 'startup', args: null}
		]
	}, (err, res, body) => {
            console.log(res.statusCode);
    });
}

function addHeatpump(config) {
	request.post(url + 'synccmds', {json: 
		[
			{ cmd: 'createObj', 'entity' : 'BufConvDev', 'val': 
				[
					{name: config.name},
					{host: null}
				],
			}, //debug stuff here to test with a normal load, needs to be replaced
			{ cmd: 'setVar', entity: config.name, 'var': 'capacity', 'val': 15000 },
			{ cmd: 'setVar', entity: config.name, 'var': 'chargingPowers', 'val': [-0, 4000] },
			{ cmd: 'setVar', entity: config.name, 'var': 'cop', 'val': 4.0 },
			{ cmd: 'setVar', entity: config.name, 'var': 'soc', 'val': 7500 },
			{ cmd: 'setVar', entity: config.name, 'var': 'initialSoC', 'val': 7500 },
			{ cmd: 'setVar', entity: config.name, 'var': 'filename', 'val': "alpg/output/demo/Heat_Profile.csv" },
			{ cmd: 'setVar', entity: config.name, 'var': 'column', 'val': config.housenumber },
			{ cmd: 'setVar', entity: config.name, 'var': 'scaling', 'val': 2 }, //debug stuff here
			{ cmd: 'setVar', entity: config.name, 'var': 'timeBase', 'val': 900 },
			{ cmd: 'setVar', entity: config.name, 'var': 'strictComfort', 'val': false },
			{ cmd: 'callFunction', entity : config.name, func: 'startup', args: null},
			{ cmd: 'callFunction', entity : config.meter, func: 'addDevice', args: {obj: config.name}},
			{ cmd: 'createObj', 'entity' : 'BufConvAuctionCtrl', 'val': 
				[
					{name: "Controller-"+config.name},
					{obj: config.name},
					{obj: "Aggregator-"+config.housenumber},
					{host: null}
				],
			},
			{ cmd: 'setVar', entity: "Controller-"+config.name, 'var': 'strictComfort', 'val': false },
			{ cmd: 'callFunction', entity : "Controller-"+config.name, func: 'startup', args: null}
		]
	}, (err, res, body) => {
            console.log(res.statusCode);
    });
}


const PORT = process.env.PORT || 3002;
http.listen(PORT, () => {
    console.log("Server running on port " + PORT );
});

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
    socket.on('disconnect', function(){
        request(url + 'control/release', {json: {clientId: socket.id}}, (err, res, body) => {

        });
        console.log('user disconnected');
      });

    socket.on('requestTick', function() {
        request(urlForTick, {json: {clientId: socket.id}}, (err, res, body) => {
            io.sockets.connected[socket.id].emit('tickResponse', body);
            // io.sockets[socket.id].emit('tickResponse', body)
        });
    });

    socket.on('requestTicks', function() {
        request(urlForTick + '/4', {json: {clientId: socket.id}}, (err, res, body) => {
            io.sockets.connected[socket.id].emit('tickResponse', body)
            if (err) {
                return console.log(err);
            }
        });
    });

    socket.on('requestControl', function() {
        request(url + 'control/request', {json: {clientId: socket.id}}, (err, res, body) => {
            if (body && body.success) {
                io.sockets.connected[socket.id].emit('obtainedControl');
            }
        })
    });

	socket.on('removeDevice', function(name) {
        request.post(url + 'remove', {json: {entity: name}}, (err, res, body) => {
	//		console.log(err, res, body);
		});
	});

	socket.on('addDevice', function(settings) {
        let endpoint = settings.endpoint;
        let config = {
            name: endpoint[0].toUpperCase() + endpoint.slice(1) + '-' + settings.deviceId +
                '-House-' + settings.housenumber,
            smart: settings.isSmart
        };

        function createSchedule(times) {
            // If you need a schedule from let's say 23 - 7, then create a job for 23-24 and 0-7.
            let schedule = [];

            for (let i = 0; i < times.length; i++) {
                const time = times[i];
                const startObj = time;

                for (let month = 0; month < 12; month++) { // Month starts at 0
                    for (let day = 1; day < 4; day++) { // Day starts at 1
                        // TODO: Fix time if user uses a different time zone
                        const startDate = new Date(2019, month, day, startObj.h, startObj.m, startObj.s);
                        const timeOffset = new Date(2019, 0, 1, 0, 0, 0);
                        const startTime = (startDate.getTime() - timeOffset.getTime()) / 1000;
                        const endTime = startTime + startObj.d;

                        schedule.push([startTime, endTime]);
                    }
                }
            }
            schedule.sort((a, b) => a[0] < b[0] ? -1 : 1);
            console.log(schedule);
            return schedule;
        }

        // function secondsToHms(d) {
        //     d = Number(d);
        //     var h = Math.floor(d / 3600);
        //     var m = Math.floor(d % 3600 / 60);
        //     var s = Math.floor(d % 3600 % 60);

        //     return {h, m, s};
        // }

        switch (settings.endpoint) {
            case 'battery':
                config.chargingPower = 12000;
                config.capacity = 6000;
                addBattery(config);
                break;
            case 'solarPanel':
                config.size = 10;
                addSolarPanel(config);
                break;
            case 'dishWasher':
                config.schedule = createSchedule([{h: 13, m: 0, s: 0, d: 5 * 60 * 60}, {h: 19, m: 0, s: 0, d: 5 * 60 * 60}]);
                addDishwasher(config);
                break;
            case 'washingMachine':
                config.schedule = createSchedule([{h: 18, m: 0, s: 0, d: 5 * 60 * 60}, {h: 23, m: 59, s: 0, d: 5 * 60 * 60}]);
                addDishwasher(config);
                break;
            case 'vehicle':
                config.chargingPower = 6000;
                config.capacity = 12000;
                config.hybrid = false;
                config.schedule = createSchedule([{h: 17, m: 0, s: 0, d: 10 * 60 * 60}]).map(x => [x[0], x[1], config.capacity]);
                addVehicle(config);
                break;
            case 'boiler':
                config.capacity = 250000;
                addBoiler(config);
                break;
            default:

        }
	});

    socket.on('editDevice', function(settings) {
        request.post(url + 'editEntity', {json: settings}, (err, res, body) => {
            // console.log(err, body);
        })
    });

    socket.on('fixCable', function(settings) {
        request.post(url + 'repairCable', {json: {name: settings.name}}, (err, res, body) => {
            // console.log(body, res.statusCode);
        });
    })

    socket.on('makeSmart', function(settings) {
        request.post(url + 'makeSmart', {json: {devices: settings.devices}}, (err, res, body) => {
            console.log(body, res.statusCode);
        });
    })

    socket.on('makeDumb', function(settings) {
        request.post(url + 'makeDumb', {json: {devices: settings.devices}}, (err, res, body) => {
            console.log(body, res.statusCode);
        });
    })
});

function addBattery(config) {
    let fullConfig = {
        parameters: [config.name],
        properties: {
            chargingPowers: [-config.chargingPower, config.chargingPower],
            capacity: config.capacity,
            initialSoC: 0.5 * config.capacity,
            soc: 0.5 * config.capacity,
            discrete: false,
            highMark: 0.8 * config.capacity,
            lowMark: 0.2 * config.capacity,
        },
        functions: []
    }

    request.post(url + 'addEntity/generic', {json: {
        entity: fullConfig,
        class: "dev.bufDev.BufDev",
        smart: config.smart,
        type: "device"}}, (err, res, body) => {
            console.log(res.statusCode);
    });
}

function addSolarPanel(config) {
    let fullConfig = {
        parameters: [config.name],
        properties: {
            size: config.size,
            efficiency: 20,
            azimuth: 180,
            inclination: 35
        },
        functions: []
    }

    request.post(url + 'addEntity/generic', {json: {
        entity: fullConfig,
        class: "dev.electricity.solarPanelDev.SolarPanelDev",
        smart: config.smart,
        type: "device"}}, (err, res, body) => {
            console.log(res.statusCode);
    });
}

function addDishwasher(config) {
    let fullConfig = {
        parameters: [config.name],
        properties: {
            profile: DEFAULT_PROFILE,
            timeBase: 60,
            strictComfort: true
        },
        functions: config.schedule.map((schedule) => { return ({name: "addJob", parameters: schedule}) } ),
    }

    request.post(url + 'addEntity/generic', {json: {
        entity: fullConfig,
        class: "dev.tsDev.TsDev",
        smart: config.smart,
        type: "device"}}, (err, res, body) => {
            console.log(res.statusCode);
    });
}

function addVehicle(config) {
    let fullConfig = {
        parameters: [config.name],
        properties: {
            chargingPowers: [-config.chargingPower, config.chargingPower],
            capacity: config.capacity,
            initialSoC: 0.5 * config.capacity,
            soc: 0.5 * config.capacity,
            discrete: false,
            highMark: 0.8 * config.capacity,
            lowMark: 0.2 * config.capacity,
            hybrid: false
        },
        functions: config.schedule.map((schedule) => { return ({name: "addJob", parameters: schedule}) } ),
    }

    request.post(url + 'addEntity/generic', {json: {
        entity: fullConfig,
        class: "dev.btsDev.BtsDev",
        smart: config.smart,
        type: "device"}}, (err, res, body) => {
            console.log(res.statusCode);
    });
}

function addBoiler(config) {
    let fullConfig = {
        parameters: [config.name],
        properties: {
            capacity: config.capacity,
            initialSoC: 0.5 * config.capacity,
            soc: 0.5 * config.capacity,
            discrete: false,
            highMark: 0.8 * config.capacity,
            lowMark: 0.2 * config.capacity,

        },
        functions: [],
    }

    request.post(url + 'addEntity/generic', {json: {
        entity: fullConfig,
        class:  "dev.bufConvDev.BufConvDev",
        smart: config.smart,
        type: "device"}}, (err, res, body) => {
            console.log(res.statusCode);
    });

}


const PORT = process.env.PORT || 3002;
http.listen(PORT, () => {
    console.log("Server running on port " + PORT );
});


const DEFAULT_PROFILE = [{'imag': 9.91720178381, 'real': 2.343792}, {'imag': 8.79153133754, 'real': 0.705584}, {'imag': 7.86720661017, 'real': 0.078676}, {'imag': 7.87400627016, 'real': 0.078744}, {'imag': 7.89440525013, 'real': 0.078948}, {'imag': 7.91480423011, 'real': 0.079152}, {'imag': 7.90120491012, 'real': 0.079016}, {'imag': 7.88080593015, 'real': 0.078812}, {'imag': 3.10574286964, 'real': 0.941108}, {'imag': 18.0981988883, 'real': 10.449}, {'imag': 1.78766247656, 'real': 4.523148}, {'imag': 15.5624864632, 'real': 34.157214}, {'imag': 70.6731270362, 'real': 155.116416}, {'imag': 72.1629803176, 'real': 158.38641}, {'imag': 67.6446776265, 'real': 158.790988}, {'imag': 72.1320090814, 'real': 158.318433}, {'imag': 67.5864385584, 'real': 158.654276}, {'imag': 109.033724507, 'real': 131.583375}, {'imag': 13.0299198193, 'real': 13.91745}, {'imag': 1.91271835851, 'real': 4.489968}, {'imag': 669.148867416, 'real': 1693.082112}, {'imag': 447.115028245, 'real': 3137.819256}, {'imag': 442.825240368, 'real': 3107.713851}, {'imag': 444.604029241, 'real': 3120.197256}, {'imag': 445.069607955, 'real': 3123.464652}, {'imag': 443.814052026, 'real': 3114.653256}, {'imag': 444.757595169, 'real': 3121.27497}, {'imag': 444.04953577, 'real': 3116.305863}, {'imag': 442.695246796, 'real': 3106.801566}, {'imag': 444.248722882, 'real': 3117.703743}, {'imag': 444.412290486, 'real': 3118.851648}, {'imag': 443.15330662, 'real': 3110.016195}, {'imag': 442.410911425, 'real': 3104.806122}, {'imag': 416.724520071, 'real': 1148.154728}, {'imag': 70.8616610914, 'real': 166.342624}, {'imag': 68.6731497838, 'real': 161.205252}, {'imag': 68.1809395169, 'real': 160.049824}, {'imag': 67.6368392593, 'real': 158.772588}, {'imag': 67.3963581543, 'real': 158.208076}, {'imag': 67.2762351774, 'real': 157.926096}, {'imag': 66.8875305491, 'real': 157.01364}, {'imag': 108.243298437, 'real': 112.30272}, {'imag': 9.35164905552, 'real': 11.65632}, {'imag': 18.4299236306, 'real': 17.569056}, {'imag': 2.10750178285, 'real': 4.947208}, {'imag': 2.012422389, 'real': 4.724016}, {'imag': 65.2075123351, 'real': 143.12025}, {'imag': 68.6408949029, 'real': 161.129536}, {'imag': 63.501604078, 'real': 160.671915}, {'imag': 12.8265693277, 'real': 23.764224}, {'imag': 62.352437012, 'real': 136.853808}, {'imag': 62.8850229849, 'real': 159.11184}, {'imag': 63.0244750664, 'real': 159.464682}, {'imag': 62.8578235805, 'real': 159.04302}, {'imag': 55.7061505818, 'real': 36.68544}, {'imag': 7.07164059421, 'real': 9.767628}, {'imag': 2.08857212612, 'real': 4.902772}, {'imag': 885.033921728, 'real': 2239.315008}, {'imag': 444.126516228, 'real': 3116.846106}, {'imag': 443.298337972, 'real': 3111.034014}, {'imag': 444.306997808, 'real': 3118.112712}, {'imag': 443.408878355, 'real': 3111.809778}, {'imag': 443.641484325, 'real': 3113.442189}, {'imag': 443.226478259, 'real': 3110.529708}, {'imag': 442.392431601, 'real': 3104.676432}, {'imag': 441.881880613, 'real': 3101.093424}, {'imag': 444.729268843, 'real': 3121.076178}, {'imag': 443.248103556, 'real': 1221.232208}, {'imag': 63.2218912841, 'real': 159.964185}, {'imag': 966.568347525, 'real': 2663.07828}, {'imag': 436.038267268, 'real': 272.524675}, {'imag': 5.82624, 'real': 7.76832}, {'imag': 1.75854256572, 'real': 3.258112}, {'imag': 1.69033685682, 'real': 3.299408}, {'imag': 1.68814824631, 'real': 3.295136}, {'imag': 1.75778260783, 'real': 3.256704}, {'imag': 1.75854256572, 'real': 3.258112}, {'imag': 1.7608224394, 'real': 3.262336}, {'imag': 807.439674778, 'real': 2224.648744}, {'imag': 587.426961418, 'real': 367.142872}, {'imag': 11.8288968082, 'real': 4.711025}]

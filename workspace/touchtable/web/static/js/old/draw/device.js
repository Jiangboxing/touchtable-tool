class Device {

	static fromDemData(device) {
		const nameToImage = {
			'SolarPanel': 'solarpanel.png',
			'Vehicle': 'car.png',
			'Battery': 'buffer.png',
			'Heatpump': 'bufferconverter.png',
			'DishWasher': 'dishwasher.png',
			'WashingMachine': 'washingmachine.png'
		}

		let deviceType = device.name.split('-')[0];
		let imageName = nameToImage[deviceType];
		let houseNum = houseNumFromName(device.name);
		let house = houses[houseNum];

		if (!imageName) {
			console.warn('unimplemented device type in images', deviceType);
			return null;
		} else {
			return new Device(imageName,
				house.x + 10 + Math.random() * (house.width - 10 - Device.size),
				house.y + 10 + Math.random() * (house.height - 10 - Device.size),
				false, house, device.name, device.name.split('-')[1]);
		}
	}

	constructor(imageName, xpos, ypos, isMoved=false, house=null, demname=null, uuid) {
		this.name = imageName;
		this.image = document.getElementById(imageName);
		this.size = Device.size;
		this.uuid = uuid || Math.floor(Math.random() * 2**32).toString(16);
		this.x = xpos;
		this.y = ypos;
		this.velocity = { x: 0, y: 0 }
		this.house = house;
		this.demname = demname;

		this.settings = imageToSettings[imageName];
		this.settingsOpen = false;

		this.movestate = isMoved
		this.grabbedPos = { x: this.size / 2, y: this.size / 2};
		this.lastPos = { x: this.x, y: this.y };

		this.lastDt = 1;
		this.lastMove = new Date();

		this.rotation = 0.5 * Math.PI;

		this.spawnTime = null;
		this.ttl = 5 * 1000;

		// When the device has existed for over this.ttl ms, shove it towards the garbage can by setting this goal
		this.goal = null;
	}

	update(dt, now) {
		if (!this.spawnTime) {
			this.spawnTime = now;
		}

		let dist = ((SCREEN_HEIGHT - this.size) / 2) - this.y
		this.rotation = (0.5 * Math.PI) + dist / (SCREEN_HEIGHT / 16)
		this.rotation = Math.max(0, Math.min(Math.PI, this.rotation));


		if (!this.movestate) {
			this.x += this.velocity.x * dt;
			this.y += this.velocity.y * dt;

			if(this.settingsOpen){
				let setting = document.getElementById(this.uuid);

				//TODO; this is the hacky solution
				if(setting != null){
					setting.style.left = settingsOffsetX(this.x) + 'px';
					setting.style.top = settingsOffsetY(this.y) + 'px';
					setting.style.transform = "rotate("+this.rotation+"rad)";
				}
			}

			this.x = Math.max(0, Math.min(SCREEN_WIDTH - this.size, this.x))
			this.y = Math.max(0, Math.min(SCREEN_HEIGHT - this.size, this.y))

			// Apply a friction force in the reverse direction of the velocity
			this.velocity.x += -this.velocity.x * dt * 2;
			this.velocity.y += -this.velocity.y * dt * 2;

			this.velocity.x = Math.abs(this.velocity.x) < 0.1 ? 0 : this.velocity.x;
			this.velocity.y = Math.abs(this.velocity.y) < 0.1 ? 0 : this.velocity.y;

			this.lastDt = dt;
		}

		if (this.goal) {
			this.velocity.x = -(this.x - this.goal.x) * 1.5 + 50;
			this.velocity.y = -(this.y - this.goal.y) * 1.5 + 50;
		}
	}

	draw() {
		ctx.save();
		ctx.translate(this.x, this.y);
		ctx.translate(this.size / 2, this.size / 2);
		ctx.rotate(this.rotation);

		ctx.beginPath();
		ctx.rect(-this.size / 2, -this.size / 2, this.size, this.size);
		ctx.stroke();

		ctx.fillStyle = "#cccccc"

		let devState = DEMDevices[this.demname]

		let r = 0xcc;
		let g = 0xcc;
		let b = 0xcc;
		if (devState) {
			let consumption = devState.consumption.ELECTRICITY;
			if (consumption) {
				if (consumption.real !== undefined) {
					consumption = consumption.real;
				}
				let modifier = Math.min(1, Math.abs(consumption / CONSUMPTION_VISUALISATION_ROOF));
				if (consumption < 0) {
					r = 0xcc - modifier * 0xcc;
					g = 0xcc + modifier * (0xff - 0xcc);
					b = r;
				} else {
					r = 0xcc + modifier * (0xff - 0xcc);
					g = 0xcc - modifier * 0xcc;
					b = g;
				}
			}
		}

		ctx.fillStyle = "#" + (r << 16 | g << 8 | b).toString(16).padStart(6, '0');
		ctx.fill();

		if (this.demname) {
			let soc = DEMDevices[this.demname].soc;
			let capacity = DEMDevices[this.demname].capacity;
			if (soc !== undefined && capacity !== undefined) {
				ctx.fillStyle = 'black';
				ctx.fillRect(-this.size / 2 - 1, this.size / 2, this.size + 2, this.size / 4 + 2);
				ctx.fillStyle = '#cccccc';
				ctx.fillRect(-this.size / 2, this.size / 2 + 1, this.size, this.size / 4);
				ctx.fillStyle = '#11ff44';
				if ((soc / capacity) < 0.1){
					ctx.fillStyle = '#ff4444';
				} else if ((soc / capacity) < 0.25){
					ctx.fillStyle = '#ff8844';
				} else if ((soc / capacity) < 0.4){
					ctx.fillStyle = '#ffff44';
				}			
				ctx.fillRect(-this.size / 2, this.size / 2 + 1, Math.min(this.size, (this.size * soc / capacity)), this.size / 4);

			}
		}


		ctx.drawImage(this.image, -this.size / 2, -this.size / 2, this.size, this.size);

		ctx.restore();
	}

	mousemove(mousex, mousey) {
		if (this.movestate) {
			this.moved = true;
			this.lastPos.x = this.x;
			this.lastPos.y = this.y;
			this.x = mousex - this.grabbedPos.x;
			this.y = mousey - this.grabbedPos.y;

			if(this.settingsOpen){
				let setting = document.getElementById(this.uuid);

				//TODO; this is the hacky solution
				if(setting != null){
					setting.style.left = settingsOffsetX(this.x) + 'px';
					setting.style.top = settingsOffsetY(this.y) + 'px';
					setting.style.transform = "rotate("+this.rotation+"rad)";
				}
			}

			this.lastMove = new Date();
			this.goal = null;
		}
	}

	isClicked(clickx, clicky) {
		return (
			clickx > this.x && clickx < this.x + this.size &&
			clicky > this.y && clicky < this.y + this.size);
	}

	grab(clickx, clicky) {
		if (!this.settingsOpen) {
			this.velocity = { x: 0, y: 0 };
			this.movestate = true;
			this.grabbedPos = {
				x: clickx - this.x,
				y: clicky - this.y
			};

			this.moved = false;
		}
	}

	release() {
		if (this.movestate) {
			this.movestate = false;
			const DECEL_TIME = 100;
			let modifier = Math.max(0, (this.lastMove - new Date()) + DECEL_TIME) / DECEL_TIME;
			this.velocity.x = (this.x - this.lastPos.x) * modifier * (1 / this.lastDt);
			this.velocity.y = (this.y - this.lastPos.y) * modifier * (1 / this.lastDt);

			if(!this.moved){
				this.showSettings();
			}

			this.moved = false;
		}
	}

	addHouse(house){
		this.house = house;
	}

	removeHouse(){
		this.house = null;
	}

	showSettings(){
		let devState = DEMDevices[this.demname]
		if (this.settings.length == 0) {
			return;
		}

		if(!this.settingsOpen && devState && this.house != null){
			let content = "";
			this.settingsOpen = true;


			content += "<div class='settings' id='"+this.uuid+"'>";
			content += `<p id=devname-${this.uuid} style="display: none">${this.name}</p>`

			this.settings.forEach(setting => {
				switch(setting){
					case SETTINGS.SIZE:
						let size = devState.size;
						content += "<div style='display: flex; justify-content: space-between'><label for=size-"+this.uuid+"> Size </label><span id='size-"+this.uuid+"-value'>"+size+' '+SETTING_TO_UNIT['size']+"</span></div>";
						content += "<input id=size-"+this.uuid+" value="+size+" type=range name=points min=1 max=50 oninput='updateValues(event)'>";
						break;
					case SETTINGS.PANELS:
						let panels = devState.panels;
						content += "<div style='display: flex; justify-content: space-between'><label for=panels-"+this.uuid+"> Panels </label><span id='panels-"+this.uuid+"-value'>"+panels+' '+SETTING_TO_UNIT['panels']+"</span></div>";
						content += "<input id=panels-"+this.uuid+" value="+panels+" type=range name=points min=1 max=30 step=1 oninput='updateValues(event)'>";
						break;
					case SETTINGS.WATTPEAK:
						let eff = devState.wattPeak;
						content += "<div style='display: flex; justify-content: space-between'><label for=wattPeak-"+this.uuid+"> Watt Peak </label><span id='wattPeak-"+this.uuid+"-value'>"+eff+' '+SETTING_TO_UNIT['wattPeak']+"</span></div>";
						content += "<input id=wattPeak-"+this.uuid+" value="+devState.wattPeak+" type=range name=wattPeak min=200 max=400 step=10 oninput='updateValues(event)'>";
						break;
					case SETTINGS.CAPACITYBUF:
						let capacitybuf = devState.capacity;
						content += "<div style='display: flex; justify-content: space-between'><label for=capacity-"+this.uuid+"> Capacity </label><span id='capacity-"+this.uuid+"-value'>"+capacitybuf+' '+SETTING_TO_UNIT['capacity']+"</span></div>";
						content += "<input id=capacity-"+this.uuid+" value="+capacitybuf+" type=range name=points min=4000 max=30000 step=2000 oninput='updateValues(event)'>";
						break;
					case SETTINGS.CHARGINGRATEBUF:
						let ratebuf = devState.chargingPowers[1];
						content += "<div style='display: flex; justify-content: space-between'><label for=chargingPowers-"+this.uuid+"> Power </label><span id='chargingPowers-"+this.uuid+"-value'>"+ratebuf+' '+SETTING_TO_UNIT['chargingPowers']+"</span></div>";
						content += "<input id=chargingPowers-"+this.uuid+" value="+ratebuf+" type=range name=points min=3000 max=11000 step=1000 oninput='updateValues(event)'>";
						break;
					case SETTINGS.CHARGINGRATEEV:
						let rateev = devState.chargingPowers[1];
						content += "<div style='display: flex; justify-content: space-between'><label for=chargingPowers-"+this.uuid+"> Power </label><span id='chargingPowers-"+this.uuid+"-value'>"+rateev+' '+SETTING_TO_UNIT['chargingPowers']+"</span></div>";
						content += "<input id=chargingPowers-"+this.uuid+" value="+rateev+" type=range name=points min=3000 max=11000 step=1000 oninput='updateValues(event)'>";
						break;
					case SETTINGS.CAPACITYEV:
						let capacityev = devState.capacity;
						content += "<div style='display: flex; justify-content: space-between'><label for=capacity-"+this.uuid+"> Capacity </label><span id='capacity-"+this.uuid+"-value'>"+capacityev+' '+SETTING_TO_UNIT['capacity']+"</span></div>";
						content += "<input id=capacity-"+this.uuid+" value="+capacityev+" type=range name=points min=20000 max=100000 step=5000 oninput='updateValues(event)'>";
						break;
					case SETTINGS.CHARGINGRATEHP:
						let rateconv = devState.chargingPowers[1];
						content += "<div style='display: flex; justify-content: space-between'><label for=chargingPowers-"+this.uuid+"> Power </label><span id='chargingPowers-"+this.uuid+"-value'>"+rateconv+' '+SETTING_TO_UNIT['chargingPowers']+"</span></div>";
						content += "<input id=chargingPowers-"+this.uuid+" value="+rateconv+" type=range name=points min=3000 max=8000 step=1000 oninput='updateValues(event)'>";
						break;
					case SETTINGS.CAPACITYHP:
						let capacityconv = devState.capacity;
						content += "<div style='display: flex; justify-content: space-between'><label for=capacity-"+this.uuid+"> Buffer capacity </label><span id='capacity-"+this.uuid+"-value'>"+capacityconv+' '+SETTING_TO_UNIT['capacity']+"</span></div>";
						content += "<input id=capacity-"+this.uuid+" value="+capacityconv+" type=range name=points min=2500 max=30000 step=2500 oninput='updateValues(event)'>";
						break;
					case SETTINGS.COPHP:
						let copconv = devState.cop;
						content += "<div style='display: flex; justify-content: space-between'><label for=cop-"+this.uuid+"> Coeffient of Performance </label><span id='cop-"+this.uuid+"-value'>"+copconv+' '+SETTING_TO_UNIT['cop']+"</span></div>";
						content += "<input id=cop-"+this.uuid+" value="+copconv+" type=range name=points min=3 max=5 step=0.2 oninput='updateValues(event)'>";
						break;
					case SETTINGS.RCHP:
						let rcconv = 6 - devState.scaling;
						content += "<div style='display: flex; justify-content: space-between'><label for=scaling-"+this.uuid+"> Insulation </label><span id='scaling-"+this.uuid+"-value'>"+rcconv+' '+SETTING_TO_UNIT['scaling']+"</span></div>";
						content += "<input id=scaling-"+this.uuid+" value="+rcconv+" type=range name=points min=1 max=5 step=1 oninput='updateValues(event)'>";
						break;
					default:
						break;
				}
			})


			content += "<button style='margin-top: 2px' onClick=closeSetting('"+this.uuid+"')> ✕ </button>";
			content += "</div>";

			document.getElementById("settings").innerHTML += content;

			let setting = document.getElementById(this.uuid);
			setting.style.left = settingsOffsetX(this.x) + 'px';
			setting.style.top = settingsOffsetY(this.y) + 'px';
		}
	}

	shouldDespawn(now){
		return new Date() - this.lastMove > this.ttl && this.house == null
	}
}

function settingsOffsetX(x) {
	return x > 0.89 * SCREEN_WIDTH ? 0.89 * SCREEN_WIDTH - 10 : x - 10;
}

function settingsOffsetY(y) {
	return y < 0.5 * SCREEN_HEIGHT ? y + (80 - Device.size/2) : y - (80 + Device.size/2);
}

function closeSetting(name){
	//should be called first since update() is called in quite short intervals
	device = devices.filter(dev => dev.uuid.includes(name))[0];
	
	if (device.settingsOpen) {
		saveSetting(name);
		let parent = document.getElementById("settings");
		let child = document.getElementById(name);
		parent.removeChild(child);
	}
	device.settingsOpen = false;
}

function saveSetting(name){
	let devnameElement = document.getElementById(`devname-${name}`);
	let devname = devnameElement.innerHTML;

	let newProperties = {};

	for (let setting of imageToSettings[devname]) {
		let settingName = SETTINGNAME[setting]
		let settingElement = document.getElementById(`${settingName}-${name}`);

		if (setting == SETTINGS.CHARGINGRATEBUF) {
			newProperties[settingName] = [-parseFloat(settingElement.value), parseFloat(settingElement.value)]
			continue;
		}
		if (setting == SETTINGS.CHARGINGRATEEV) {
			newProperties[settingName] = [0, parseFloat(settingElement.value)]
			continue;
		}
		if (setting == SETTINGS.CHARGINGRATEHP) {
			newProperties[settingName] = [0, parseFloat(settingElement.value)]
			continue;
		}
		if (setting == SETTINGS.RCHP) {
			newProperties[settingName] = 6 - parseFloat(settingElement.value)
			continue;
		}


		newProperties[settingName] = settingElement.value;
	}

	let device = devices.filter(dev => dev.demname && dev.demname.includes(name))[0];

	updateSettings(device.demname, newProperties);
}



var SETTINGS = {
	CHARGINGRATE: 1,
	CAPACITY: 2,
	SIZE: 3,
	HYBRID: 4,
	EFFICIENCY: 5,
	INCLINATION: 6,
	AZIMUTH: 7,
	PANELS: 8,
	WATTPEAK: 9,
	COP: 10,
	CHARGINGRATEBUF: 11,
	CAPACITYBUF: 12,
	CHARGINGRATEEV: 13,
	CAPACITYEV: 14,
	CHARGINGRATEHP: 15,
	CAPACITYHP: 16,
	COPHP: 17,
	RCHP: 18,
}

// Convert WBV internal setting names to DEMKit property names
var SETTINGNAME = [
	'',
	'chargingPowers',
	'capacity',
	'size',
	'hybrid',
	'efficiency',
	'inclination',
	'azimuth',
	'panels',
	'wattPeak',
	'cop',
	'chargingPowers',
	'capacity',
	'chargingPowers',
	'capacity',
	'chargingPowers',
	'capacity',
	'cop',
	'scaling',
]

const SETTING_TO_UNIT = {
	'efficiency': '%',
	'chargingPowers': 'W',
	'capacity': 'Wh',
	'size': 'm²',
	'panels': '',
	'wattPeak': 'Wp',
	'cop': '',
	'scaling': 'm²K/W'
}


Device.size = 60;

const deviceTypes = ["buffer.png", "bufferconverter.png", "car.png", "dishwasher.png", "solarpanel.png", "washingmachine.png"]

const devices = [];

const imageToEndpoint = {
	"buffer.png": "battery",
	"bufferconverter.png": "heatpump",
	"car.png": "vehicle",
	"dishwasher.png": "dishWasher",
	"solarpanel.png": "solarPanel",
	"washingmachine.png": "washingMachine"
}

const imageToSettings = {
	"buffer.png": [SETTINGS.CAPACITYBUF, SETTINGS.CHARGINGRATEBUF],
	"bufferconverter.png": [SETTINGS.CAPACITYHP, SETTINGS.CHARGINGRATEHP, SETTINGS.COPHP, SETTINGS.RCHP],
	"car.png": [SETTINGS.CAPACITYEV, SETTINGS.CHARGINGRATEEV],
	"dishwasher.png": [],
	"solarpanel.png": [SETTINGS.PANELS, SETTINGS.WATTPEAK],
	"washingmachine.png": []
}

let staticDevices = deviceTypes.map((name, index) => {
	return new Device(name,
		Math.floor((index / 18 + 0.35) * SCREEN_WIDTH),
		Math.floor(SCREEN_HEIGHT / 2 - Device.size / 2));
});

function updateValues(e) {
	let valueId = e.target.id + '-value';
	let valueElement = document.getElementById(valueId);

	if (valueElement) {
		let unit = SETTING_TO_UNIT[e.target.id.split('-')[0]];
		valueElement.innerHTML = e.target.value + ' ' + unit;
	}

}

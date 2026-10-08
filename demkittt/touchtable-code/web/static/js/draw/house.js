let coordinates = [
    [10,10], [735,10], [1462,10],
    [1462, 870], [735, 870], [10, 870]
]

class House {
    constructor(name, number, devices = [], isSmart) {
        this.name = name;
        this.number = number;
        this.devices = devices;
        this.isSmart = isSmart;

        this.x = coordinates[number][0];
        this.y = coordinates[number][1];
        this.width = 450;
        this.height = 200;
		
		this.power = 100;
		this.meter = 0;
    }

    draw() {
        ctx.fillStyle = "#b0abaf";
        ctx.fillRect(this.x, this.y, this.width, this.height);
		
		let r = 0xcc;
		let g = 0xcc;
		let b = 0xcc;
		let consumption = this.power;
		if (consumption) {
			if (consumption.real !== undefined) {
				consumption = consumption.real;
			}
			let modifier = Math.min(1, Math.abs(consumption / 10000));
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
		
		ctx.fillStyle = "#222222";
        ctx.fillRect(this.x-8, this.y-8, this.width+16, this.height+16);
		
		ctx.fillStyle = "#" + (r << 16 | g << 8 | b).toString(16).padStart(6, '0');
		ctx.fillRect(this.x-6, this.y-6, this.width+12, this.height+12);
		
		ctx.fillStyle = "#b0abaf";
        ctx.fillRect(this.x, this.y, this.width, this.height);
    }

    addDevice(device) {
        this.devices.push(device);
    }

    removeDevice(device) {
        let index = this.devices.indexOf(device);

        this.devices.splice(index,1);
    }

    isInsideHouse(x, y) {
        if(this.x < x && this.x+this.width > x){
            if(this.y < y && this.y+this.height > y){
                return true;
            }
        }

        return false;
    }
}

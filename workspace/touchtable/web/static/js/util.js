

function length(v) {
	return Math.sqrt(v.x ** 2 + v.y ** 2);
}

function normalize(v) {
	return multscalar(v, 1 / length(v))
}

function multscalar(v, s) {
	return {
		x: v.x * s,
		y: v.y * s
	}
}

function add(v1, v2) {
	return {
		x: v1.x + v2.x,
		y: v1.y + v2.y
	}
}


function houseNumFromName(name) {
	return parseInt(name.split('-House-').pop());
}

function idFromName(name) {
	return name.split('-')[1];
}

function uuidv4() {
	return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
		var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
		return v.toString(16);
	});
}

function colorToHex(color) {
	return '#' + (Math.floor(color.r) << 16 | Math.floor(color.g) << 8 | Math.floor(color.b)).toString(16).padStart(6, '0');
}

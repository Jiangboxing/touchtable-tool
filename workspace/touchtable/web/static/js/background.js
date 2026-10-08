function getSeason(date) {
    let month = date.getMonth();

    if (month >= 3 && month <= 5) {
        return 'spring';
    } else if (month >= 6 && month <= 8) {
        return 'summer';
    } else if (month >= 9 && month <= 11) {
        return 'fall';
    } else {
        return 'winter';
    }
}

function isNight() {
    if (DEMData) {
        let sun = DEMData.environments.filter(env => env.name == "Sun")[0];
        return sun.elevation < 0;
    } else {
        return false;
    }
}

function elevation() {
    if (DEMData) {
        let sun = DEMData.environments.filter(env => env.name == "Sun")[0];
        return sun.elevation;
    } else {
        return -90;
    }
}

class Background {

    constructor(){
        this.dayImage = "images/background-winter.png";
        this.nightImage = "images/background-winter-night.png";
		this.currentImage = this.dayImage;
        this.season = 'winter';
    }

    update(dt, now) {
        if (DEMData) {
            let image = "background-";
            let date = new Date(DEMData.host.currentTime * 1000);
			
            image += getSeason(date);
            let gray = isPaused() ? '-gray' : '';
            this.dayImage = 'images/'+ image + gray + '.png';
            this.nightImage = 'images/'+ image + '-night' + gray + '.png';
        }
    }

    draw(){
		document.body.style.backgroundImage = "url('"+this.dayImage+"')";
        document.getElementById("bg").style.backgroundImage = "url('"+this.nightImage+"')";
		document.getElementById("bg").style.opacity = Math.min(Math.max(0, (1 - elevation() / 10) / 2), 1);
    }
}

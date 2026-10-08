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
        this.dayImage = document.getElementById("background-summer.png");
        this.nightImage = document.getElementById("background-summer-night.png");
        this.season = 'summer';
    }

    update(dt, now) {
        if (DEMData) {
            let image = "background-";

            let date = new Date(DEMData.host.currentTime * 1000);

            image += getSeason(date);


            if (this.dayImage.id != image) {
                let gray = isPaused() ? '-gray' : '';
                this.dayImage = document.getElementById(image + gray + '.png');
                this.nightImage = document.getElementById(image + '-night' + gray + '.png');
            }
        }
    }

    draw(){
        ctx.drawImage(this.dayImage, 0,0)
        ctx.globalAlpha = Math.min(Math.max(0, (1 - elevation() / 10) / 2), 1);
        ctx.drawImage(this.nightImage, 0,0)
        ctx.globalAlpha = 1;
    }
}

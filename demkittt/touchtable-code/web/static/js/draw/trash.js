class Trash{
    constructor(){
        this.imageName = "trash.png"
        this.image = document.getElementById(this.imageName);
        this.size = 75;
        this.x = GARBAGE_CAN_POS.x;
        this.y = GARBAGE_CAN_POS.y;

        this.rotation = 0.5 * Math.PI;
    }

    draw(){
        ctx.save();
		ctx.translate(this.x, this.y);
        ctx.translate(this.size / 2, this.size / 2);
        ctx.rotate(this.rotation);

		ctx.beginPath();
		ctx.rect(-this.size / 2, -this.size / 2, this.size, this.size);
		ctx.stroke();
		ctx.fillStyle = "#cccccc"
		ctx.fill();
		ctx.drawImage(this.image, -this.size / 2, -this.size / 2, this.size, this.size);

		ctx.restore();
    }

    intersect(x, y){
        return (this.x < x && this.x+this.size > x) && (this.y < y && this.y+this.size > y);
    }


}

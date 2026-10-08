    var angleScale = {
		angle: 0,
		scale: 1
	}
	
	var zmax = 100;
	
	function dragMoveListener (event) {
        console.log('dragMoveListener');
        var target = event.target
            // keep the dragged position in the data-x/data-y attributes
            x = (parseFloat(target.getAttribute('data-x')) || 0) + event.dx,
            y = (parseFloat(target.getAttribute('data-y')) || 0) + event.dy;
			s = (parseFloat(target.getAttribute('data-s')) || 100);
			z = (parseFloat(target.getAttribute('data-z')) || 1);
			if (event.scale) {
				console.log(event.scale)
				s = s * (1+(event.ds));
				z = z * event.scale;
				z = Math.max(0.66, Math.min(2.0, z));
				//console.log(s)
			}
		
		/*
		dist = ((1080) / 2) - y
		rotation = (0.5 * Math.PI) + dist / (1080 / 16)
		console.log(rotation)
		rotation = Math.max(0, Math.min(Math.PI, rotation));
		console.log(y)
		console.log(dist)
		console.log(rotation)
        // translate the element
        target.style.webkitTransform =
            target.style.transform =
                'translate(' + x + 'px, ' + y + 'px) scale('+z+ ') rotate('+rotation+'rad)'; //'+s+')';
		*/
		
		dist = ((1080 - (z*60)) / 2) - (y+510);
		rotation = (0.5 * Math.PI) + dist / (1080 / 12);
		rotation = Math.max(0, Math.min(Math.PI, rotation));
        // translate the element
        target.style.webkitTransform =
            target.style.transform =
                'translate(' + x + 'px, ' + y + 'px) scale('+z+ ') rotate('+rotation+'rad)'; //'+s+')';
		
		//target.style.height = s

        // update the position attributes
        target.setAttribute('data-x', x);
        target.setAttribute('data-y', y);
		target.setAttribute('data-s', s);
		//target.setAttribute('data-z', z);
		
		target.style.zIndex = zmax+1;
		zmax = zmax+1;
		
		p = Math.round(s)
		//target.style.width = p+'px';
		//target.style.height = p+'px';
		
		

		//target.style.transform = "rotate("+this.rotation+"rad)";
    }
    
    function reset () {
		scaleElement.style.webkitTransform =
			scaleElement.style.transform =
			'scale(1)'

		angleScale.angle = 0
		angleScale.scale = 1
	}
	
	// this is used later in the resizing and gesture demos
	window.dragMoveListener = dragMoveListener

    // target elements with the "draggable" class
    interact('.x')
        .draggable({
            // enable inertial throwing
            inertia: true,
            // keep the element within the area of it's parent
            restrict: {
                restriction: "parent",
                endOnly: false,
                elementRect: { top: 0, left: 0, bottom: 1, right: 1 }
            },
            
            // enable autoScroll
            autoScroll: true,

            onstart: function (event) {
                console.log('onstart');

            },

            // call this function on every dragmove event
            onmove: dragMoveListener,
            // call this function on every dragend event
            onend: function (event) {
                console.log('onend');
            }
        })
	
	interact('.draggable')
		.gesturable({
			onstart: function (event) {
			  console.log('onstart2');
			  //angleScale.angle -= event.angle;
			},
		
			onmove: function (event) {
				console.log('onmove2');
				// document.body.appendChild(new Text(event.scale))
				/*var currentAngle = event.angle + angleScale.angle
				var currentScale = event.scale * angleScale.scale
				var scaleElement = event.target.parentElement.children[0];
				console.log(scaleElement)
				//var target = event.target

				scaleElement.style.webkitTransform =
				scaleElement.style.transform =
					'scale(' + currentScale + ')'
				*/
				// uses the dragMoveListener from the draggable demo above
				dragMoveListener(event)
			},
			onend: function (event) {
				console.log('onend2');
				//var scaleElement = event.target.parentElement.children[0];
				//angleScale.angle = angleScale.angle + event.angle
				//angleScale.scale = angleScale.scale * event.scale
				//angleScale.angle = angleScale.angle + event.angle
				//angleScale.scale = angleScale.scale * event.scale
				var target = event.target
					z = (parseFloat(target.getAttribute('data-z')) || 1);
					z = z * event.scale
					z = Math.max(0.66, Math.min(2.0, z));
					console.log(z)
					
					target.setAttribute('data-z', z);
			}
		})
		.draggable({
            // enable inertial throwing
            inertia: true,
            // keep the element within the area of it's parent
            restrict: {
                restriction: "parent",
                endOnly: false,
                elementRect: { top: 0, left: 0, bottom: 1, right: 1 }
            },
            
            // enable autoScroll
            autoScroll: true,

            onstart: function (event) {
                console.log('onstart');

            },

            // call this function on every dragmove event
            onmove: dragMoveListener,
            // call this function on every dragend event
            onend: function (event) {
                console.log('onend');
            }
        })
		
	    .on('tap', function (event) {
			event.currentTarget.classList.toggle('switch-bg');
			console.log('ontap');
			event.preventDefault();
		  })		
		
		
	interact('.house').dropzone({
	  // only accept elements matching this CSS selector
	  // Require a 75% element overlap for a drop to be possible
	  overlap: 0.75,

	  // listen for drop related events:

	  ondropactivate: function (event) {
		// add active dropzone feedback
		event.target.classList.add('drop-active')
	  },
	  ondragenter: function (event) {
		var draggableElement = event.relatedTarget
		var dropzoneElement = event.target

		// feedback the possibility of a drop
		dropzoneElement.classList.add('drop-target')
		draggableElement.classList.add('can-drop')
	  },
	  ondragleave: function (event) {
		// remove the drop feedback style
		event.target.classList.remove('drop-target')
		event.relatedTarget.classList.remove('can-drop')
	  },
	  ondrop: function (event) {
	  },
	  ondropdeactivate: function (event) {
		// remove active dropzone feedback
		event.target.classList.remove('drop-active')
		event.target.classList.remove('drop-target')
	  }
	})
	
	
    

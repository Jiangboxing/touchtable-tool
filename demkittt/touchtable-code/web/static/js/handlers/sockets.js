
$(function () {
    socket.on('data', function(data){
        let first = false;
        if (!DEMData) {
            first = true;
        }
        DEMData = data


		for (let deviceState of DEMData.devices) {
            if (deviceState.name.startsWith('Load-')) {
				//for (let house of houses) {
				//	if (house.number == parseInt(deviceState.name.charAt(11)) ) {
				//		console.log("Hello world!"); 
				//		house.power = deviceState.consumption.ELECTRICITY;
				//	}
				//}
				continue;
            }
			if (deviceState.name.startsWith('SmartMeter-House-')) {
				//console.log(deviceState.name.charAt(11)); 
				for (let house of houses) {
					if (house.number == parseInt(deviceState.name.charAt(17)) ) {
						house.power = deviceState.consumption.ELECTRICITY;
					}
				}
				continue;
            }
			

            // New device from an outside source
            if (devices.filter(dev => dev.uuid == idFromName(deviceState.name)).length == 0) {
                let deviceObject = Device.fromDemData(deviceState);
                if (deviceObject) {
                    devices.push(deviceObject);
                    deviceObject.house.addDevice(deviceObject);
                }
            }

            if (!Object.keys(DEMDevices).includes(deviceState.name)) {
                devices.filter(dev => dev.uuid == idFromName(deviceState.name))[0].demname = deviceState.name;
            }
            DEMDevices[deviceState.name] = deviceState;
		}

        if (first) {
            network.setNetwork(data.network);

            for (let house of houses) {
                let smartDevices = [];
                for (let device of house.devices) {
                    for (let controller of DEMData.controllers) {
                        if (idFromName(controller.name) == idFromName(device.demname)) {
                            console.log(device.demname, controller.name)
                            smartDevices.push(device);
                        }
                    }
                }
                if (smartDevices.length == house.devices.length && house.devices.length > 0) {
                    house.isSmart = true;
                }
            }
        }

        // Check if a device has been removed from DEMKit, and remove it here as well
        let idsOfDevicesInDEMKit = DEMData.devices.map(dev => idFromName(dev.name));
        let deletedDevices = devices.filter(dev => dev.house != null && !idsOfDevicesInDEMKit.includes(dev.uuid));

        for (let device of deletedDevices) {
            device.house.removeDevice(device);
            devices.splice(devices.indexOf(device), 1);
        }

        network.updateNetwork(data.network);

        let clock = document.getElementById('clock')
        if (clock) {
            clock.innerHTML = new Date(DEMData.host.currentTime * 1000);
        }
    })

    socket.on('tickResponse', function(response) {
        let playButton = document.getElementById('playButton');
    });

    socket.on('obtainedControl', function(response) {
        isMaster = true;
        doTick();
    });
});

function removeDeviceFromHouse(device){
    socket.emit('remove', device.name)
}

function doTick() {
    socket.emit('requestTick');
}

function removeDeviceFromDEMKit(name) {
    socket.emit('removeDevice', name)
}

function requestControl() {
    socket.emit('requestControl');
}

function addDeviceToDEMKit(endpoint, housenumber, deviceId, isSmart) {
    socket.emit('addDevice', {endpoint, housenumber, deviceId, isSmart});
}

function updateSettings(deviceName, newProperties) {
    socket.emit('editDevice', {properties: newProperties, name: deviceName});
}

function fixCable(name) {
    let cable = network.cables.filter(cable => cable.name == name)[0];
    if (cable) {
        cable.burned = false;
    }

    socket.emit('fixCable', { name });
}

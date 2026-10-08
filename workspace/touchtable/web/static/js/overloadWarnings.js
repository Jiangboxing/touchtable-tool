const HOUSE_OVERLOAD_WARNING_THRESHOLD = 0.85;

function findHouseConnectionCable(houseNumber) {
	if (typeof network == "undefined" || !network || !Array.isArray(network.cables)) {
		return null;
	}

	let connectionName = "houseconnection-" + houseNumber;

	return network.cables.find(cable => cable.nodes.some(node => node.name == connectionName));
}

function updateHouseOverloadWarnings() {
	if (typeof refreshGameficationUI == "function") {
		refreshGameficationUI();
	}
}

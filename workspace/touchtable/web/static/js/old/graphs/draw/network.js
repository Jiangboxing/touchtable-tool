
var networkChart = null;
var data = []

function setupNetwork(network){

    labels = [];

    for(n in network){
        labels.append(n.name);

        data.append([])
    }    

    var ctx = document.getElementById('chart-network').getContext('2d');
    networkChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'current',
                data: data,
            }]
        },
        options: {
            scales: {
                yAxes: [{
                    ticks: {
                        beginAtZero: true
                    }
                }]
            }
        }
    });
}

function addData(network){

    for(n in network){
        
    }

}
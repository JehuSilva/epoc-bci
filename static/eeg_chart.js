$(document).ready(function(){
    // Chart.defaults.line.spanGaps = true;
    // Defining colors

    var color = Chart.helpers.color;

    var chartColors = {
        red:    'rgb(255, 99, 132)',
        orange: 'rgb(255, 159, 64)',
        yellow: 'rgb(255, 205, 86)',
        green:  'rgb(75, 192, 80)',
        blue:   'rgb(54, 162, 235)',
        purple: 'rgb(153, 102, 255)',
        grey:   'rgb(201, 203, 207)'
    };

    var config = {
        type: 'line',
        data: {
            datasets: [{
                label: 'F1',
                backgroundColor: color(chartColors.red).alpha(0.1).rgbString(),
                borderColor: chartColors.red,
                fill: false,
                lineTension: 0,
                borderDash: [10, 20],
                data: [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
            }]
        },
        options: {
            scales: {
                xxAxes: {
                    type: 'time',
                    distribution: 'series'
                }
            }
        }
    };

    function addData(chart, label, data) {
        chart.data.labels.push(label);
        chart.data.datasets.forEach((dataset) => {
            dataset.data.push(data);
        });
        chart.update(0);
    }
    
    function removeData(chart) {
        chart.data.labels.pop();
        chart.data.datasets.forEach((dataset) => {
            dataset.data.pop();
        });
        chart.update();
    }
    

    function updateChartData(chart, data, dataSetIndex){
      chart.data.datasets[dataSetIndex].data = data;
      chart.update();
    }
    
    onload = function() {
        var canvas = document.getElementById('eeg_chart').getContext('2d');
        window.chart = new Chart(canvas, config);
    };


    var socket = io.connect('http://' + document.domain + ':' + location.port + '/stream');

    socket.on('data', function(msg) {
        console.log('hello');
        // console.log(msg.sensors.F3.value);
        // data_array.push(msg.number);
        // data_array.shift();
        // console.log(data_array);
        // addData(window.chart,'F1',msg.number)
    });

});

var MILLNAMES = ['', 'k', 'M', 'B', 'T', 'P', 'E', 'Z', 'Y'];

function millify(n) {
  var significantPart = Math.floor(Math.log10(Math.abs(n)) / 3);
  var millidx = Math.max(0, Math.min(MILLNAMES.length - 1, significantPart));
  var pretty = n / Math.pow(10, 3 * millidx);
  var decimal = pretty % 1 === 0 ? 2 : 3;
  return parseFloat(pretty.toPrecision(decimal)) + '' + MILLNAMES[millidx];
}

function initializeChart(chartId, data) {
  var config = {
    type: 'line',
    data: {
      datasets: [
        {
          backgroundColor: 'rgba(52, 144, 220, 0.5)',
          borderColor: 'rgba(52, 144, 220, 1)',
          fill: true,
          data: data
        }
      ]
    },
    options: {
      legend: {
        display: false
      },
      tooltips: {
        displayColors: false,
        callbacks: {
          label: function(item, data) {
            var contracts = data.datasets[0].data[item.index].contracts
            return [
              'Contratos: ' + contracts,
              'Total: $' + item.yLabel.toLocaleString()
            ];
          }
        }
      },
      scales: {
        xAxes: [
          {
            display: false,
            type: 'time',
            time: {
              tooltipFormat: 'll'
            }
          }
        ],
        yAxes: [
          {
            display: true,
            ticks: {
              beginAtZero: true,
              maxTicksLimit: 5,
              callback: function(value) {
                return '$' + millify(value);
              }
            }
          }
        ]
      }
    }
  };

  var ctx = document.getElementById(chartId).getContext('2d');
  return new Chart(ctx, config);
}

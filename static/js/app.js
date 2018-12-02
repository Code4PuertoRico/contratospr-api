var MILLNAMES = ['', 'k', 'M', 'B', 'T', 'P', 'E', 'Z', 'Y'];

function millify(n) {
  var significantPart = Math.floor(Math.log10(Math.abs(n)) / 3);
  var millidx = Math.max(0, Math.min(MILLNAMES.length - 1, significantPart));
  var pretty = n / Math.pow(10, 3 * millidx);
  var decimal = pretty % 1 === 0 ? 2 : 3;
  return parseFloat(pretty.toPrecision(decimal)) + '' + MILLNAMES[millidx];
}

var DEFAULT_POINT_BG_COLOR = 'rgba(52, 144, 220, 0.5)';
var DEFAULT_POINT_RADIUS = 3;
var SELECTED_POINT_BG_COLOR = 'rgba(52, 144, 220, 1)';
var SELECTED_POINT_RADIUS = 5;

function initializeChart(chartId, data) {
  var config = {
    type: 'line',
    data: {
      datasets: [
        {
          backgroundColor: 'rgba(52, 144, 220, 0.5)',
          borderColor: 'rgba(52, 144, 220, 1)',
          pointBackgroundColor: data.map(() => DEFAULT_POINT_BG_COLOR),
          pointRadius: data.map(() => DEFAULT_POINT_RADIUS),
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
            var contracts = data.datasets[0].data[item.index].contracts;
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
      },
      onClick: function(e) {
        var firstPoint = this.getElementAtEvent(e)[0];
        var dataset = this.data.datasets[0];

        var contractsElements = document
          .getElementById('contracts-list')
          .querySelectorAll('a');
        var contracts = Array.from(contractsElements);

        if (firstPoint) {
          var value = dataset.data[firstPoint._index];

          dataset.pointBackgroundColor = data.map(() => DEFAULT_POINT_BG_COLOR);
          dataset.pointBackgroundColor[firstPoint._index] = SELECTED_POINT_BG_COLOR;
          dataset.pointRadius = data.map(() => DEFAULT_POINT_RADIUS);
          dataset.pointRadius[firstPoint._index] = SELECTED_POINT_RADIUS;
          this.update({ duration: 0 });

          contracts.forEach(function(contract) {
            if (value.x === contract.getAttribute('data-date')) {
              contract.style.display = '';
            } else {
              contract.style.display = 'none';
            }
          });
        } else {
          dataset.pointBackgroundColor = data.map(() => DEFAULT_POINT_BG_COLOR);
          dataset.pointRadius = data.map(() => DEFAULT_POINT_RADIUS);
          this.update({ duration: 0 });

          contracts.forEach(function(contract) {
            contract.style.display = '';
          });
        }
      }
    }
  };

  var canvas = document.getElementById(chartId);
  var ctx = canvas.getContext('2d');
  return new Chart(ctx, config);
}

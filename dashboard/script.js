const chartsContainer = document.getElementById('charts-container');
const apiBaseUrl = '/api/v1';

async function fetchData(pair, timeframe) {
    try {
        const response = await fetch(`${apiBaseUrl}/pair_candles?pair=${encodeURIComponent(pair)}&timeframe=${timeframe}&limit=100`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching data:', error);
    }
}

function createChart(chartData, condition, timeframe) {
    const chartContainer = document.createElement('div');
    chartContainer.classList.add('chart-container');
    const canvas = document.createElement('canvas');
    chartContainer.appendChild(canvas);
    chartsContainer.appendChild(chartContainer);

    new Chart(canvas, {
        type: 'line',
        data: {
            labels: chartData.map(d => new Date(d.date).toLocaleTimeString()),
            datasets: [{
                label: `${condition} (${timeframe})`,
                data: chartData.map(d => d[condition]),
                borderColor: '#00bfff',
                borderWidth: 1,
                fill: false,
                tension: 0.1
            }]
        },
        options: {
            scales: {
                y: {
                    min: -1,
                    max: 1
                }
            },
            plugins: {
                legend: {
                    labels: {
                        color: '#f2f2f2'
                    }
                }
            }
        }
    });
}

async function updateCharts() {
    const pairs = ['PAXG/USDT:USDT'];
    const timeframes = ['15m', '1h'];
    const conditions = ['rsi_condition', 'stoch_condition', 'cloud_condition', 'line_condition', 'macd_condition', 'adx_condition', 'bb_condition'];

    chartsContainer.innerHTML = '';

    for (const pair of pairs) {
        for (const timeframe of timeframes) {
            const data = await fetchData(pair, timeframe);
            if (data) {
                const chartData = data.data.map(d => {
                    const row = {};
                    data.columns.forEach((col, i) => {
                        row[col] = d[i];
                    });
                    return row;
                });

                for (const condition of conditions) {
                    const conditionTimeframe = `${condition}_${timeframe.replace('m', '')}`;
                    if (chartData[0].hasOwnProperty(condition) || chartData[0].hasOwnProperty(conditionTimeframe)) {
                         createChart(chartData, chartData[0].hasOwnProperty(conditionTimeframe) ? conditionTimeframe : condition, timeframe);
                    }
                }
            }
        }
    }
}

updateCharts();
setInterval(updateCharts, 60000);
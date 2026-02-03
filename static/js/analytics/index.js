    let trafficChart, revenueTypeChart, airlineChart, airportChart;

    const chartColors = {
        primary: '#3b82f6',
        green: '#22c55e',
        yellow: '#eab308',
        red: '#ef4444',
        purple: '#a855f7',
        blue: '#06b6d4'
    };

    async function initCharts() {
        await Promise.all([
            loadTrafficChart(),
            loadRevenueTypeChart(),
            loadAirlineChart(),
            loadAirportChart()
        ]);
    }

    async function loadTrafficChart() {
        const days = document.getElementById('traffic-period').value;

        try {
            const response = await fetch(`/analytics/api/traffic/daily?days=${days}`);
            const data = await response.json();

            const ctx = document.getElementById('trafficChart').getContext('2d');

            if (trafficChart) trafficChart.destroy();

            trafficChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.map(d => d.date),
                    datasets: [{
                        label: 'Survols',
                        data: data.map(d => d.count),
                        borderColor: chartColors.primary,
                        backgroundColor: chartColors.primary + '20',
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        x: {
                            grid: { color: 'rgba(255,255,255,0.1)' },
                            ticks: { color: '#9ca3af' }
                        },
                        y: {
                            grid: { color: 'rgba(255,255,255,0.1)' },
                            ticks: { color: '#9ca3af' },
                            beginAtZero: true
                        }
                    }
                }
            });
        } catch (e) {
            console.error('Error loading traffic chart:', e);
        }
    }

    async function loadRevenueTypeChart() {
        try {
            const response = await fetch('/analytics/api/revenue/by-type');
            const data = await response.json();

            const ctx = document.getElementById('revenueTypeChart').getContext('2d');

            if (revenueTypeChart) revenueTypeChart.destroy();

            const typeLabels = {
                'overflight': 'Survols',
                'landing': 'Atterrissages',
                'parking': 'Stationnement',
                'other': 'Autres'
            };

            revenueTypeChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: data.map(d => typeLabels[d.type] || d.type),
                    datasets: [{
                        data: data.map(d => d.revenue),
                        backgroundColor: [chartColors.primary, chartColors.green, chartColors.yellow, chartColors.purple]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: { color: '#9ca3af' }
                        }
                    }
                }
            });
        } catch (e) {
            console.error('Error loading revenue type chart:', e);
        }
    }

    async function loadAirlineChart() {
        try {
            const response = await fetch('/analytics/api/revenue/by-airline');
            const data = await response.json();

            const ctx = document.getElementById('airlineChart').getContext('2d');

            if (airlineChart) airlineChart.destroy();

            airlineChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.map(d => d.code || d.airline.substring(0, 10)),
                    datasets: [{
                        label: 'Revenus ($)',
                        data: data.map(d => d.revenue),
                        backgroundColor: chartColors.green
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    indexAxis: 'y',
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        x: {
                            grid: { color: 'rgba(255,255,255,0.1)' },
                            ticks: { color: '#9ca3af' }
                        },
                        y: {
                            grid: { display: false },
                            ticks: { color: '#9ca3af' }
                        }
                    }
                }
            });
        } catch (e) {
            console.error('Error loading airline chart:', e);
        }
    }

    async function loadAirportChart() {
        try {
            const response = await fetch('/analytics/api/airports/traffic');
            const data = await response.json();

            const ctx = document.getElementById('airportChart').getContext('2d');

            if (airportChart) airportChart.destroy();

            airportChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.map(d => d.airport),
                    datasets: [
                        {
                            label: 'Arrivées',
                            data: data.map(d => d.arrivals),
                            backgroundColor: chartColors.primary
                        },
                        {
                            label: 'Départs',
                            data: data.map(d => d.departures),
                            backgroundColor: chartColors.yellow
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: { color: '#9ca3af' }
                        }
                    },
                    scales: {
                        x: {
                            grid: { display: false },
                            ticks: { color: '#9ca3af' }
                        },
                        y: {
                            grid: { color: 'rgba(255,255,255,0.1)' },
                            ticks: { color: '#9ca3af' },
                            beginAtZero: true
                        }
                    }
                }
            });
        } catch (e) {
            console.error('Error loading airport chart:', e);
        }
    }

    function updateTrafficChart() {
        loadTrafficChart();
    }

    function exportData(format) {
        const type = document.getElementById('export-type').value;
        const start = document.getElementById('export-start').value;
        const end = document.getElementById('export-end').value;

        let url = `/analytics/export/${format}?type=${type}`;
        if (start) url += `&start=${start}`;
        if (end) url += `&end=${end}`;

        window.location.href = url;
    }

    document.addEventListener('DOMContentLoaded', initCharts);

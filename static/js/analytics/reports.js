    function setDates(range) {
        const today = new Date();
        const endStr = today.toISOString().split('T')[0];
        let start = new Date();

        if (range === 'today') {
            // start is today
        } else if (range === 'week') {
            start.setDate(today.getDate() - 7);
        } else if (range === 'month') {
            start.setDate(today.getDate() - 30);
        }

        const startStr = start.toISOString().split('T')[0];

        document.getElementById('start_date').value = startStr;
        document.getElementById('end_date').value = endStr;
    }

    // Chart
    document.addEventListener('DOMContentLoaded', function() {
        const ctx = document.getElementById('reportTrafficChart').getContext('2d');
        const data = window.analyticsReportsContext.trafficData;

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.map(d => d.date),
                datasets: [{
                    label: 'Vols',
                    data: data.map(d => d.count),
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { grid: { color: 'rgba(255,255,255,0.1)' }, ticks: { color: '#9ca3af' } },
                    y: { grid: { color: 'rgba(255,255,255,0.1)' }, ticks: { color: '#9ca3af' }, beginAtZero: true }
                },
                plugins: { legend: { display: false } }
            }
        });
    });

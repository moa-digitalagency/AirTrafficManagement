    const FREE_PARKING_HOURS = 1;
    const PARKING_RATE_PER_HOUR = 25;
    const i18n = window.radarTerminalContext.i18n;

    function updateParkingTimers() {
        document.querySelectorAll('.parking-timer').forEach(el => {
            const arrival = el.dataset.arrival;
            if (!arrival) {
                el.textContent = '--:--:--';
                return;
            }

            const arrivalTime = new Date(arrival);
            const now = new Date();
            const diffMs = now - arrivalTime;
            const diffSecs = Math.floor(diffMs / 1000);

            const hours = Math.floor(diffSecs / 3600);
            const mins = Math.floor((diffSecs % 3600) / 60);
            const secs = diffSecs % 60;

            el.textContent = `${String(hours).padStart(2, '0')}:${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;

            const flightId = el.id.replace('parking-', '');
            const billableEl = document.getElementById(`billable-${flightId}`);

            if (hours >= FREE_PARKING_HOURS) {
                const billableHours = hours - FREE_PARKING_HOURS + (mins > 0 || secs > 0 ? 1 : 0);
                const amount = billableHours * PARKING_RATE_PER_HOUR;
                billableEl.innerHTML = `<span class="text-yellow-400">$${amount.toFixed(2)}</span>`;
                el.classList.add('text-yellow-400');
                el.classList.remove('text-blue-400');
            } else {
                const remaining = (FREE_PARKING_HOURS * 3600) - diffSecs;
                const remMins = Math.floor(remaining / 60);
                billableEl.innerHTML = `<span class="text-green-400">${i18n.terminal.free} (${remMins}m ${i18n.terminal.remaining})</span>`;
                el.classList.add('text-blue-400');
                el.classList.remove('text-yellow-400');
            }
        });

        let totalHours = 0;
        document.querySelectorAll('.parking-timer').forEach(el => {
            const text = el.textContent;
            const match = text.match(/(\d+):/);
            if (match) totalHours += parseInt(match[1]);
        });
        document.getElementById('total-parking-hours').textContent = `${totalHours}h`;
    }

    function refreshQueue() {
        window.location.reload();
    }

    function trackFlight(flightId) {
        window.location.href = `/radar?focus=${flightId}`;
    }

    function confirmLanding(flightId) {
        if (!confirm(i18n.terminal.confirm_landing)) return;

        fetch(`/api/flights/${flightId}/land`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.location.reload();
            } else {
                const prefix = i18n.common.error.generic || 'Error';
                const unknown = i18n.common.error.unknown || 'Unknown error';
                alert(prefix + ': ' + (data.error || unknown));
            }
        })
        .catch(e => console.error('Error:', e));
    }

    function recordDeparture(flightId) {
        if (!confirm(i18n.terminal.confirm_departure)) return;

        fetch(`/api/flights/${flightId}/depart`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.location.reload();
            } else {
                const prefix = i18n.common.error.generic || 'Error';
                const unknown = i18n.common.error.unknown || 'Unknown error';
                alert(prefix + ': ' + (data.error || unknown));
            }
        })
        .catch(e => console.error('Error:', e));
    }

    function generateParkingInvoice(flightId) {
        window.location.href = `/invoices/create?landing_id=${flightId}`;
    }

    function selectAirport(icaoCode) {
        window.location.href = `/radar/terminal?airport=${icaoCode}`;
    }

    setInterval(updateParkingTimers, 1000);
    document.addEventListener('DOMContentLoaded', updateParkingTimers);

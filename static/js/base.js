/* * Nom de l'application : ATM-RDC
 * Description : Source file: base.js
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
 */

// XSS Protection Utility
function escapeHtml(text) {
    if (typeof text !== 'string') return text;
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
window.escapeHtml = escapeHtml;

function updateTime() {
    const now = new Date();
    const utc = now.toISOString().substr(11, 8);
    const el = document.getElementById('current-time');
    if (el) el.textContent = utc;
}
setInterval(updateTime, 1000);
updateTime();

if (window.baseContext && window.baseContext.isAuthenticated) {
    let lastNotificationCount = 0;

    // Request browser notification permission
    if ("Notification" in window && Notification.permission !== "granted") {
        Notification.requestPermission();
    }

    async function updateNotifications() {
        try {
            // Get count
            const countRes = await fetch('/notifications/count');
            const countData = await countRes.json();
            const count = countData.count;

            const countEl = document.getElementById('notification-count');
            if (countEl) {
                countEl.textContent = count;
                if (count > 0) {
                    countEl.classList.remove('hidden');
                    countEl.classList.add('flex');
                } else {
                    countEl.classList.add('hidden');
                    countEl.classList.remove('flex');
                }
            }

            // If new notifications arrived, show browser notification or toast
            if (count > lastNotificationCount) {
                fetchRecentNotifications();
            }
            lastNotificationCount = count;

        } catch (e) {
            console.error('Error fetching notifications:', e);
        }
    }

    async function fetchRecentNotifications() {
        try {
            const res = await fetch('/notifications/?unread_only=true&limit=1');
            const data = await res.json();
            if (data.length > 0) {
                const notif = data[0];
                showToast(notif);

                // Browser notification
                if ("Notification" in window && Notification.permission === "granted") {
                    new Notification(notif.title, {
                        body: notif.message,
                        icon: '/static/img/logo.png' // Adjust if needed
                    });
                }
            }
        } catch(e) {}
    }

    function showToast(notification) {
        // Create toast element
        const toast = document.createElement('div');
        toast.className = 'fixed bottom-4 right-4 bg-dark-300 border border-dark-100 p-4 rounded-xl shadow-lg z-50 flex items-start gap-3 max-w-sm transform transition-all duration-300 translate-y-10 opacity-0';
        toast.innerHTML = `
            <div class="text-primary-400 mt-1"><i class="${escapeHtml(notification.icon) || 'fas fa-info-circle'}"></i></div>
            <div class="flex-1">
                <h4 class="text-sm font-semibold text-white">${escapeHtml(notification.title)}</h4>
                <p class="text-xs text-gray-400 mt-1">${escapeHtml(notification.message)}</p>
            </div>
            <button onclick="this.parentElement.remove()" class="text-gray-500 hover:text-white"><i class="fas fa-times"></i></button>
        `;
        document.body.appendChild(toast);

        // Animate in
        requestAnimationFrame(() => {
            toast.classList.remove('translate-y-10', 'opacity-0');
        });

        // Remove after 5s
        setTimeout(() => {
            toast.classList.add('translate-y-10', 'opacity-0');
            setTimeout(() => toast.remove(), 300);
        }, 5000);
    }

    async function toggleNotifications() {
        const menu = document.getElementById('notifications-menu');
        const list = document.getElementById('notifications-list');
        menu.classList.toggle('hidden');

        if (!menu.classList.contains('hidden')) {
            // Load notifications
            try {
                const res = await fetch('/notifications/');
                const data = await res.json();

                if (data.length === 0) {
                    list.innerHTML = '<div class="p-4 text-center text-gray-500 text-sm">Aucune notification</div>';
                } else {
                    list.innerHTML = data.map(n => `
                        <div class="p-3 border-b border-dark-100 hover:bg-dark-300 transition-colors ${n.is_read ? 'opacity-60' : ''}">
                            <div class="flex items-start gap-3">
                                <div class="text-primary-400 mt-1"><i class="${escapeHtml(n.icon) || 'fas fa-info-circle'}"></i></div>
                                <div class="flex-1">
                                    <h4 class="text-sm font-semibold text-white">${escapeHtml(n.title)}</h4>
                                    <p class="text-xs text-gray-400 mt-1">${escapeHtml(n.message)}</p>
                                    <div class="flex items-center gap-2 mt-2">
                                        <span class="text-xs text-gray-600">${new Date(n.created_at).toLocaleString()}</span>
                                        ${n.link ? `<a href="${escapeHtml(n.link)}" class="text-xs text-primary-400 hover:underline">Voir</a>` : ''}
                                    </div>
                                </div>
                                ${!n.is_read ? `
                                <button onclick="markRead(${n.id})" class="text-xs text-primary-400" title="Marquer comme lu"><i class="fas fa-check"></i></button>
                                ` : ''}
                            </div>
                        </div>
                    `).join('');
                }
            } catch (e) {
                list.innerHTML = '<div class="p-4 text-center text-red-400 text-sm">Erreur de chargement</div>';
            }
        }
    }

    // Make available globally
    window.toggleNotifications = toggleNotifications;

    async function markRead(id) {
        try {
            await fetch('/notifications/mark-read', {
                method: 'POST',
                headers: {'Content-Type': 'application/json', 'X-CSRFToken': window.baseContext.csrfToken},
                body: JSON.stringify({id: id})
            });
            toggleNotifications(); // Reload list
            updateNotifications(); // Update count
        } catch(e) {}
    }
    window.markRead = markRead;

    async function markAllRead() {
        try {
            await fetch('/notifications/mark-read', {
                method: 'POST',
                headers: {'Content-Type': 'application/json', 'X-CSRFToken': window.baseContext.csrfToken},
                body: JSON.stringify({id: 'all'})
            });
            toggleNotifications();
            updateNotifications();
        } catch(e) {}
    }
    window.markAllRead = markAllRead;

    // Close dropdown when clicking outside
    document.addEventListener('click', function(e) {
        const container = document.getElementById('notifications-dropdown-container');
        const menu = document.getElementById('notifications-menu');
        if (container && !container.contains(e.target) && !menu.classList.contains('hidden')) {
            menu.classList.add('hidden');
        }
    });

    setInterval(updateNotifications, 30000);
    updateNotifications();
}

// System Status Logic
let systemActive = true; // Default

async function initSystemStatus() {
    try {
        const res = await fetch('/api/system/status');
        const data = await res.json();
        systemActive = data.active;
        updateSystemUI(systemActive);
    } catch(e) {
        console.error('Failed to fetch system status', e);
    }
}

function updateSystemUI(active) {
    const btn = document.getElementById('system-switch-btn');
    const badge = document.getElementById('system-status-badge');

    // Button UI Config (Solid)
    const btnOnClass = 'bg-green-600 text-white hover:bg-green-500 border-green-500 shadow-lg shadow-green-900/50';
    const btnOffClass = 'bg-red-600 text-white hover:bg-red-500 border-red-500 shadow-lg shadow-red-900/50';

    // Badge UI Config (Subtle)
    const badgeOnClass = 'bg-green-500/20 text-green-400 border-green-500/30';
    const badgeOffClass = 'bg-red-500/20 text-red-400 border-red-500/30';

    const onText = 'Système : ACTIF';
    const offText = 'Système : ARRÊT';

    if (btn) {
        btn.disabled = false;
        const text = btn.querySelector('#system-status-text');
        const icon = btn.querySelector('i');

        btn.className = `flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium transition-all duration-300 border ${active ? btnOnClass : btnOffClass}`;
        text.textContent = active ? onText : offText;

        if (active) {
             btn.classList.add('animate-pulse');
             icon.className = 'fas fa-power-off';
        } else {
             btn.classList.remove('animate-pulse');
             icon.className = 'fas fa-power-off';
        }
    }

    if (badge) {
        const text = badge.querySelector('#system-status-text-badge');
        badge.className = `flex items-center gap-2 px-3 py-1.5 rounded-full text-sm transition-all duration-300 border ${active ? badgeOnClass : badgeOffClass}`;
        text.textContent = active ? onText : offText;
    }
}

function toggleSystemStatus() {
    const modal = document.getElementById('system-confirm-modal');
    const title = document.getElementById('modal-title');
    const msg = document.getElementById('modal-message');
    const confirmBtn = document.getElementById('confirm-system-btn');
    const iconContainer = document.getElementById('modal-icon-container');
    const icon = iconContainer.querySelector('i');

    if (systemActive) {
        // Turn OFF
        title.textContent = "Arrêter le système ?";
        msg.textContent = "Voulez-vous arrêter tout le système ? La surveillance, la facturation et le Bot seront suspendus.";
        confirmBtn.className = "inline-flex w-full justify-center rounded-md bg-red-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-red-500 sm:ml-3 sm:w-auto";
        iconContainer.className = "mx-auto flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full bg-red-100 sm:mx-0 sm:h-10 sm:w-10";
        icon.className = "fas fa-power-off text-red-600";
    } else {
        // Turn ON
        title.textContent = "Démarrer le système ?";
        msg.textContent = "Démarrer les services ATM-RDC ?";
        confirmBtn.className = "inline-flex w-full justify-center rounded-md bg-green-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-green-500 sm:ml-3 sm:w-auto";
        iconContainer.className = "mx-auto flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full bg-green-100 sm:mx-0 sm:h-10 sm:w-10";
        icon.className = "fas fa-bolt text-green-600";
    }

    // Bind click
    confirmBtn.onclick = async () => {
        confirmBtn.disabled = true;
        confirmBtn.textContent = "Traitement...";

        try {
            const res = await fetch('/api/system/status', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': window.baseContext.csrfToken
                },
                body: JSON.stringify({ active: !systemActive })
            });
            const data = await res.json();

            if (data.success) {
                systemActive = data.active;
                updateSystemUI(systemActive);
                closeSystemModal();
            } else {
                alert('Erreur: ' + (data.error || 'Unknown error'));
            }
        } catch(e) {
            alert('Erreur de connexion');
        } finally {
            confirmBtn.disabled = false;
        }
    };

    modal.classList.remove('hidden');
}

function closeSystemModal() {
    document.getElementById('system-confirm-modal').classList.add('hidden');
}

// Init
if (window.baseContext && window.baseContext.isAuthenticated) {
    initSystemStatus();
}

// Make global
window.toggleSystemStatus = toggleSystemStatus;
window.closeSystemModal = closeSystemModal;

 function openDeleteModal(ticketId, ticketKey, ticketTitle, deleteUrl) {
            document.getElementById('deleteTicketKey').textContent  = ticketKey;
            document.getElementById('deleteTicketTitle').textContent = ticketTitle;
            document.getElementById('deleteTicketForm').action      = deleteUrl; // ← ici
            $('#deleteTicketModal').modal('show');
        }

function openEditModal(ticketId, ticketKey, editUrl) {
    document.getElementById('editTicketKey').textContent = ticketKey;
    document.getElementById('editTicketFormContainer').innerHTML =
        '<div class="text-center py-4"><i class="fas fa-spinner fa-spin" style="font-size:24px;color:#6b778c;"></i></div>';

    $('#editTicketModal').modal('show');

    fetch(editUrl, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
        .then(r => r.text())
        .then(html => {
            document.getElementById('editTicketFormContainer').innerHTML = html;
        })
        .catch(() => {
            document.getElementById('editTicketFormContainer').innerHTML =
                '<p class="text-danger text-center">Failed to load form.</p>';
        });
}



function openDropdown(event, btn) {
    event.stopPropagation();

    document.querySelectorAll('.dropdown-menu.show').forEach(d => d.classList.remove('show'));

    const menu = btn.nextElementSibling;
    const rect = btn.getBoundingClientRect();

    menu.style.position = 'fixed';
    menu.style.top      = rect.bottom + 4 + 'px';
    menu.style.left     = (rect.right - 180) + 'px';
    menu.style.zIndex   = '9999';
    menu.classList.toggle('show');
}

// Ferme le dropdown si on clique ailleurs
document.addEventListener('click', function () {
    document.querySelectorAll('.dropdown-menu.show').forEach(d => d.classList.remove('show'));
});




let currentDrawerTicketId = null;

function openTicketDrawer(ticketId, drawerUrl) {
    const drawer  = document.getElementById('ticketDrawer');
    const overlay = document.getElementById('tdrOverlay');
    const loading = document.getElementById('tdrLoading');
    const content = document.getElementById('tdrContent');

    // Highlight la ligne active
    document.querySelectorAll('.ticket-row').forEach(r => r.classList.remove('drawer-active'));
    const row = document.querySelector(`.ticket-row[data-ticket-id="${ticketId}"]`);
    if (row) row.classList.add('drawer-active');

    // Ouvre le drawer avec spinner
    loading.style.display = 'flex';
    content.innerHTML = '';
    drawer.classList.add('open');
    overlay.classList.add('active');
    currentDrawerTicketId = ticketId;

    // Charge le contenu en AJAX
    fetch(drawerUrl, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(r => r.text())
    .then(html => {
        loading.style.display = 'none';
        content.innerHTML = html;
    })
    .catch(() => {
        loading.style.display = 'none';
        content.innerHTML = '<div class="p-4 text-danger">Failed to load ticket details.</div>';
    });
}

function closeTicketDrawer() {
    document.getElementById('ticketDrawer').classList.remove('open');
    document.getElementById('tdrOverlay').classList.remove('active');
    document.querySelectorAll('.ticket-row').forEach(r => r.classList.remove('drawer-active'));
    currentDrawerTicketId = null;
}

// Fermer avec Escape
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') closeTicketDrawer();
});

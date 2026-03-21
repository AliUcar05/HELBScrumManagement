function openDeleteModal(ticketId, ticketKey, ticketTitle, deleteUrl) {
    document.getElementById('deleteTicketKey').textContent  = ticketKey;
    document.getElementById('deleteTicketTitle').textContent = ticketTitle;
    document.getElementById('deleteTicketForm').action      = deleteUrl;
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

document.addEventListener('click', function (e) {
    // Ferme les dropdowns
    document.querySelectorAll('.dropdown-menu.show').forEach(d => d.classList.remove('show'));
    // Ferme le type picker si on clique ailleurs
    const picker = document.getElementById('typePicker');
    if (picker && !picker.classList.contains('hidden')) {
        if (!picker.contains(e.target) && !document.getElementById('inlineTypeSelector').contains(e.target)) {
            picker.classList.add('hidden');
        }
    }
});

// ===== TICKET DRAWER =====

let currentDrawerTicketId = null;

function openTicketDrawer(ticketId, drawerUrl) {
    const drawer  = document.getElementById('ticketDrawer');
    const overlay = document.getElementById('tdrOverlay');
    const loading = document.getElementById('tdrLoading');
    const content = document.getElementById('tdrContent');

    document.querySelectorAll('.ticket-row').forEach(r => r.classList.remove('drawer-active'));
    const row = document.querySelector(`.ticket-row[data-ticket-id="${ticketId}"]`);
    if (row) row.classList.add('drawer-active');

    loading.style.display = 'flex';
    content.innerHTML = '';
    drawer.classList.add('open');
    overlay.classList.add('active');
    currentDrawerTicketId = ticketId;

    fetch(drawerUrl, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
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

document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') closeTicketDrawer();
});

// ===== TABLE WIDTH FIX =====

$(document).ready(function() {
    function fixEmptyTableWidth() {
        var $table = $('table');
        var $tbody = $('#backlog-tbody');
        if ($tbody.children().length === 1 && $('.empty-state').length > 0) {
            $table.css('min-width', '1200px');
            $('thead').css('visibility', 'visible');
        }
    }
    fixEmptyTableWidth();
    $(window).resize(fixEmptyTableWidth);
});

// ===== INLINE CREATE ISSUE =====

const TICKET_TYPES = [
    { value: 'story',    label: 'Story',    icon: 'fas fa-bookmark',      color: '#36b37e' },
    { value: 'bug',      label: 'Bug',      icon: 'fas fa-bug',           color: '#de350b' },
    { value: 'task',     label: 'Task',     icon: 'fas fa-check-square',  color: '#42526e' },
    { value: 'epic',     label: 'Epic',     icon: 'fas fa-bolt',          color: '#5243aa' },
];

let selectedType = TICKET_TYPES[0]; // Story par défaut

function renderTypeIcon() {
    const selector = document.getElementById('inlineTypeSelector');
    if (!selector) return;
    selector.innerHTML = `<i class="${selectedType.icon}" style="color:${selectedType.color};font-size:16px;"></i>`;
    selector.title = selectedType.label;

    // Met à jour le label dans le footer
    const label = document.getElementById('inlineTypeLabel');
    if (label) label.textContent = selectedType.label;
}

function toggleTypePicker(event) {
    event.stopPropagation();
    const picker = document.getElementById('typePicker');
    if (!picker) return;

    if (!picker.classList.contains('hidden')) {
        picker.classList.add('hidden');
        return;
    }

    // Positionner en fixed par rapport au bouton pour éviter le clipping
    const btn = document.getElementById('inlineTypeSelector');
    const rect = btn.getBoundingClientRect();
    picker.style.top  = (rect.bottom + 4) + 'px';
    picker.style.left = rect.left + 'px';

    picker.classList.remove('hidden');
}

function selectType(value) {
    selectedType = TICKET_TYPES.find(t => t.value === value) || TICKET_TYPES[0];
    renderTypeIcon();
    document.getElementById('typePicker').classList.add('hidden');
}

function showInlineCreate() {
    document.getElementById('createIssueTriggerRow').style.display = 'none';
    const inlineRow = document.getElementById('createIssueInlineRow');
    inlineRow.style.display = '';
    renderTypeIcon();
    setTimeout(() => {
        document.getElementById('inlineCreateInput').focus();
    }, 50);
}

function hideInlineCreate() {
    document.getElementById('createIssueInlineRow').style.display = 'none';
    document.getElementById('createIssueTriggerRow').style.display = '';
    document.getElementById('inlineCreateInput').value = '';
    const picker = document.getElementById('typePicker');
    if (picker) picker.classList.add('hidden');
}

function handleInlineCreateKey(event) {
    if (event.key === 'Enter') {
        quickCreateIssue();
    } else if (event.key === 'Escape') {
        hideInlineCreate();
    }
}

function quickCreateIssue() {
    const input = document.getElementById('inlineCreateInput');
    if (!input || !input.value.trim()) {
        $('#globalCreateTicketModal').modal('show');
        return;
    }
    // TICKET_CREATE_URL est défini dans le template HTML
    const url = TICKET_CREATE_URL + '?title=' + encodeURIComponent(input.value) + '&type=' + selectedType.value;
    window.location.href = url;
}

function moveToSprint(ticketId) {
    var form = document.getElementById('moveToSprintModal');
    if (form) {
        document.getElementById('moveToSprintForm').action = 
            '/projects/' + PROJECT_PK + '/tickets/' + ticketId + '/add-to-sprint/';
        $('#moveToSprintModal').modal('show');
    }
}


function doRemoveFromSprint(ticketId) {
    if (!confirm('Move this ticket back to the backlog?')) return;

    // Créer un formulaire pour envoyer la requête POST
    var form = document.createElement('form');
    form.method = 'POST';
    form.action = '/projects/' + PROJECT_PK + '/ticket/remove-from-sprint/';

    // Ajouter CSRF token
    var csrfInput = document.createElement('input');
    csrfInput.type = 'hidden';
    csrfInput.name = 'csrfmiddlewaretoken';
    csrfInput.value = CSRF_TOKEN;
    form.appendChild(csrfInput);

    // Ajouter ticket_id
    var ticketInput = document.createElement('input');
    ticketInput.type = 'hidden';
    ticketInput.name = 'ticket_id';
    ticketInput.value = ticketId;
    form.appendChild(ticketInput);

    document.body.appendChild(form);
    form.submit();
}
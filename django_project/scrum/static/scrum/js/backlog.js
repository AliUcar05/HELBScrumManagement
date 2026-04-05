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

var currentMtsTicketId = null;

function moveToSprint(ticketId) {
    currentMtsTicketId = ticketId;
    $('#moveToSprintModal').modal('show');
}


function addTicketToSprint(ticketId, sprintId) {
    console.log('ticketId:', ticketId, 'sprintId:', sprintId);

    var form = document.createElement('form');
    form.method = 'POST';
    form.action = '/projects/' + PROJECT_PK + '/tickets/' + ticketId + '/add-to-sprint/';
    
    var csrf = document.createElement('input');
    csrf.type = 'hidden';
    csrf.name = 'csrfmiddlewaretoken';
    csrf.value = CSRF_TOKEN;
    form.appendChild(csrf);
    
    var sprint = document.createElement('input');
    sprint.type = 'hidden';
    sprint.name = 'sprint_id';
    sprint.value = sprintId;
    form.appendChild(sprint);
    
    document.body.appendChild(form);
    form.submit();
}


function removeTicketFromSprint(ticketId, sprintId) {
    var form = document.getElementById('confirmDeleteForm');
    
    var existing = form.querySelector('input[name="ticket_id"]');
    if (existing) existing.remove();
    var existingSprint = form.querySelector('input[name="sprint_id"]');
    if (existingSprint) existingSprint.remove();
    
    var input = document.createElement('input');
    input.type = 'hidden';
    input.name = 'ticket_id';
    input.value = ticketId;
    form.appendChild(input);

    var sprintInput = document.createElement('input');
    sprintInput.type = 'hidden';
    sprintInput.name = 'sprint_id';
    sprintInput.value = sprintId;
    form.appendChild(sprintInput);

    confirmDelete({
        title: 'Remove from sprint?',
        message: 'This issue will be moved back to the backlog.',
        warning: 'You can add it to a sprint again later.',
        action: '/projects/' + PROJECT_PK + '/ticket/remove-from-sprint/',
        btnLabel: 'Remove'
    });
}

// ==================== DRAG AND DROP FUNCTIONS ====================

let draggedElement = null;

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return '';
}

function getDragItems(container) {
    return Array.from(container.querySelectorAll('.drag-ticket-card, .backlog-draggable-row'));
}

function getInsertAfterElement(container, y) {
    const elements = getDragItems(container).filter(el => el !== draggedElement);
    let closest = { offset: Number.NEGATIVE_INFINITY, element: null };

    elements.forEach(el => {
        const box = el.getBoundingClientRect();
        const offset = y - box.top - box.height / 2;
        if (offset < 0 && offset > closest.offset) {
            closest = { offset, element: el };
        }
    });

    return closest.element;
}

function insertDraggedElement(container, y) {
    if (!draggedElement) return;
    const afterElement = getInsertAfterElement(container, y);
    if (afterElement) {
        container.insertBefore(draggedElement, afterElement);
    } else {
        container.appendChild(draggedElement);
    }
}

function refreshSprintEmptyState(sprintBody) {
    if (!sprintBody) return;
    const inner = sprintBody.querySelector('.spt-dropzone-inner') || sprintBody;
    const rows = inner.querySelectorAll('.drag-ticket-card');
    const empty = inner.querySelector('.spt-empty');

    if (rows.length === 0) {
        if (!empty) {
            const block = document.createElement('div');
            block.className = 'spt-empty';
            block.innerHTML = '<p>Plan your sprint. Drag and drop issues from the backlog below.</p>';
            inner.appendChild(block);
        }
    } else if (empty) {
        empty.remove();
    }
}

function refreshBacklogEmptyState() {
    const tbody = document.getElementById('backlog-tbody');
    if (!tbody) return;
    const rows = Array.from(tbody.querySelectorAll('.backlog-draggable-row'));
    const empty = tbody.querySelector('.empty-state')?.closest('tr');
    if (rows.length === 0) {
        if (!empty) {
            const tr = document.createElement('tr');
            tr.innerHTML = '<td colspan="11" class="empty-state"><i class="fas fa-clipboard-list"></i><p>No issues in backlog</p></tr>';
            const triggerRow = document.getElementById('createIssueTriggerRow');
            if (triggerRow) {
                tbody.insertBefore(tr, triggerRow);
            } else {
                tbody.appendChild(tr);
            }
        }
    } else if (empty && empty !== rows[0]?.closest('tr')) {
        empty.remove();
    }
}

async function syncSprintOrder(sprintId, sprintBody) {
    if (!sprintId || !sprintBody) return;
    const inner = sprintBody.querySelector('.spt-dropzone-inner') || sprintBody;
    const orderedTicketIds = Array.from(inner.querySelectorAll('.drag-ticket-card'))
        .map(el => el.dataset.ticketId);

    const formData = new URLSearchParams();
    orderedTicketIds.forEach(id => formData.append('ordered_ticket_ids[]', id));

    try {
        const response = await fetch(`/projects/${PROJECT_PK}/sprints/${sprintId}/reorder/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
            },
            body: formData.toString(),
        });
        const data = await response.json();
        if (!data.success) {
            console.error('Reorder error:', data.error);
        }
    } catch (error) {
        console.error('Sync sprint order error:', error);
    }
}

function moveRowToBacklog(tbody, element) {
    const triggerRow = document.getElementById('createIssueTriggerRow');
    if (triggerRow) {
        tbody.insertBefore(element, triggerRow);
    } else {
        tbody.appendChild(element);
    }
    element.dataset.dragOrigin = 'backlog';
    delete element.dataset.sprintId;
}

function moveCardToSprint(sprintBody, element, y) {
    const inner = sprintBody.querySelector('.spt-dropzone-inner') || sprintBody;
    const empty = inner.querySelector('.spt-empty');
    if (empty) empty.remove();
    insertDraggedElement(inner, y);
    element.dataset.dragOrigin = 'sprint';
    element.dataset.sprintId = sprintBody.dataset.sprintId;
}

function handleDragStart(e) {
    draggedElement = this;
    this.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', this.dataset.ticketId || '');
}

function handleDragEnd(e) {
    this.classList.remove('dragging');
    draggedElement = null;
}

function handleDragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    this.classList.add('drag-over');
}

function handleDragLeave(e) {
    this.classList.remove('drag-over');
}

async function handleDrop(e) {
    e.preventDefault();
    this.classList.remove('drag-over');

    if (!draggedElement) return;

    const ticketId = draggedElement.dataset.ticketId;
    const origin = draggedElement.dataset.dragOrigin;
    const target = this.dataset.target;
    const originContainer = draggedElement.parentElement;
    const originSprintBody = draggedElement.closest('.sprint-dropzone');
    const originSprintId = draggedElement.dataset.sprintId || '';

    if (!ticketId || !target) return;

    try {
        if (target === 'sprint') {
            const sprintId = this.dataset.sprintId;
            const url = `/projects/${PROJECT_PK}/tickets/${ticketId}/add-to-sprint/`;

            moveCardToSprint(this, draggedElement, e.clientY);
            refreshSprintEmptyState(originSprintBody);

            const formData = new URLSearchParams();
            formData.append('sprint_id', sprintId);
            if (origin === 'sprint' && originSprintId) {
                formData.append('source_sprint_id', originSprintId);
            }

            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
                },
                body: formData.toString(),
            });

            const data = await response.json();
            if (!data.success) {
                if (originContainer) originContainer.appendChild(draggedElement);
                refreshSprintEmptyState(this);
                refreshSprintEmptyState(originSprintBody);
                alert(data.error || 'Unable to move ticket to sprint.');
                return;
            }

            if (origin === 'backlog') {
                refreshBacklogEmptyState();
            }

            await syncSprintOrder(sprintId, this);
            if (origin === 'sprint' && originSprintId && originSprintId !== sprintId) {
                await syncSprintOrder(originSprintId, originSprintBody);
            }
        }

        if (target === 'backlog' && origin === 'sprint') {
            const sprintId = originSprintId || this.dataset.sprintId || "";

            moveRowToBacklog(this, draggedElement);
            refreshSprintEmptyState(originSprintBody);
            refreshBacklogEmptyState();

            const formData = new URLSearchParams();
            formData.append('ticket_id', ticketId);
            if (sprintId) {
                formData.append('sprint_id', sprintId);
            }

            const response = await fetch(`/projects/${PROJECT_PK}/ticket/remove-from-sprint/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
                },
                body: formData.toString(),
            });

            const data = await response.json();
            if (!data.success) {
                if (originContainer) originContainer.appendChild(draggedElement);
                refreshSprintEmptyState(originSprintBody);
                refreshBacklogEmptyState();
                alert(data.error || 'Unable to move ticket back to backlog.');
                return;
            }

            if (sprintId) {
                await syncSprintOrder(sprintId, originSprintBody);
            }
        }
    } catch (error) {
        console.error('Drop error:', error);
        alert('An error occurred during drag and drop.');
    }
}

function attachDragAndDrop() {
    const draggables = document.querySelectorAll('.drag-ticket-card, .backlog-draggable-row');
    draggables.forEach(el => {
        el.setAttribute('draggable', 'true');
        el.removeEventListener('dragstart', handleDragStart);
        el.removeEventListener('dragend', handleDragEnd);
        el.addEventListener('dragstart', handleDragStart);
        el.addEventListener('dragend', handleDragEnd);
    });

    const dropZones = document.querySelectorAll('.sprint-dropzone, #backlog-tbody');
    dropZones.forEach(zone => {
        zone.removeEventListener('dragover', handleDragOver);
        zone.removeEventListener('dragleave', handleDragLeave);
        zone.removeEventListener('drop', handleDrop);
        zone.addEventListener('dragover', handleDragOver);
        zone.addEventListener('dragleave', handleDragLeave);
        zone.addEventListener('drop', handleDrop);
    });
}

// Initialiser le drag and drop au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    attachDragAndDrop();

    // Observer les changements du DOM pour attacher les événements aux nouveaux éléments
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes.length) {
                attachDragAndDrop();
            }
        });
    });
    observer.observe(document.body, { childList: true, subtree: true });
});
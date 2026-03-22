// ===== TICKET DRAWER =====

let currentDrawerTicketId = null;

function openTicketDrawer(ticketId, drawerUrl) {
    var drawer  = document.getElementById('ticketDrawer');
    var loading = document.getElementById('tdrLoading');
    var content = document.getElementById('tdrContent');
    if (!drawer) return;

    document.querySelectorAll('.ticket-row, .it-row, .spt-row').forEach(function(r) {
        r.classList.remove('drawer-active');
    });
    var row = document.querySelector('[data-ticket-id="' + ticketId + '"]');
    if (row) row.classList.add('drawer-active');

    loading.style.display = 'flex';
    content.innerHTML = '';
    drawer.classList.add('open');

    // Push main content left — Jira style
    var pushEl = document.getElementById('backlogMain') ||
                 document.querySelector('.backlog-main') ||
                 document.querySelector('.backlog-layout') ||
                 document.querySelector('.it-layout') ||
                 document.querySelector('.project-content');
    if (pushEl) {
        pushEl.style.transition = 'padding-right .25s cubic-bezier(.4,0,.2,1)';
        pushEl.style.paddingRight = '488px';
    }

    currentDrawerTicketId = ticketId;
    currentDrawerUrl      = drawerUrl;

    fetch(drawerUrl, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
        .then(function(r) { return r.text(); })
        .then(function(html) {
            loading.style.display = 'none';
            content.innerHTML = html;
            content.querySelectorAll('script').forEach(function(s) {
                var ns = document.createElement('script');
                ns.textContent = s.textContent;
                document.body.appendChild(ns);
            });
        })
        .catch(function() {
            loading.style.display = 'none';
            content.innerHTML = '<div style="padding:24px;color:#de350b;text-align:center;">Failed to load issue.</div>';
        });
}

function closeTicketDrawer() {
    var drawer = document.getElementById('ticketDrawer');
    if (drawer) drawer.classList.remove('open');

    // Restore pushed content
    var pushEl = document.getElementById('backlogMain') ||
                 document.querySelector('.backlog-main') ||
                 document.querySelector('.backlog-layout') ||
                 document.querySelector('.it-layout') ||
                 document.querySelector('.project-content');
    if (pushEl) pushEl.style.paddingRight = '';

    document.querySelectorAll('.ticket-row, .it-row, .spt-row').forEach(function(r) {
        r.classList.remove('drawer-active');
    });
    currentDrawerTicketId = null;
    currentDrawerUrl      = null;
}

document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') closeTicketDrawer();
});

// ===== INLINE FIELD EDITING =====

function editField(fieldName) {
    const ticketId  = document.getElementById('tdrInner').dataset.ticketId;
    const projectId = document.getElementById('tdrInner').dataset.projectId;
    const element   = event.target.closest('[onclick^="editField"]') || event.target;

    let currentValue = '';
    let fieldType    = 'text';
    let options      = [];

    switch (fieldName) {
        case 'title':
            currentValue = document.getElementById('tdrTitle').textContent.trim();
            break;
        case 'description':
            currentValue = document.getElementById('tdrDescription').innerText.trim();
            if (currentValue === 'Add a description...') currentValue = '';
            fieldType = 'textarea';
            break;
        case 'priority':
            currentValue = element.classList.contains('priority')
                ? (element.className.match(/priority-(\w+)/) || [])[1] || 'medium'
                : 'medium';
            fieldType = 'select';
            options = [
                { value: 'highest', label: 'Highest' },
                { value: 'high',    label: 'High'    },
                { value: 'medium',  label: 'Medium'  },
                { value: 'low',     label: 'Low'     },
                { value: 'lowest',  label: 'Lowest'  },
            ];
            break;
        case 'status':
            currentValue = element.classList.contains('tdr-status')
                ? (element.className.match(/status-(\w+)/) || [])[1] || 'todo'
                : 'todo';
            fieldType = 'select';
            options = [
                { value: 'todo',        label: 'To Do'      },
                { value: 'in_progress', label: 'In Progress'},
                { value: 'in_review',   label: 'In Review'  },
                { value: 'done',        label: 'Done'       },
                { value: 'blocked',     label: 'Blocked'    },
            ];
            break;
        case 'story_points':
            const pts = element.querySelector('.tdr-points');
            currentValue = pts ? pts.textContent.trim() : '';
            if (currentValue === '—') currentValue = '';
            fieldType = 'number';
            break;
        case 'assignee':
            fetchAssignees(projectId, ticketId, element);
            return;
        default:
            return;
    }

    // Build input HTML
    let inputHtml = '';
    if (fieldType === 'select') {
        inputHtml = '<select class="form-control form-control-sm">';
        options.forEach(opt => {
            const sel = opt.value === currentValue ? 'selected' : '';
            inputHtml += `<option value="${opt.value}" ${sel}>${opt.label}</option>`;
        });
        inputHtml += '</select>';
    } else if (fieldType === 'textarea') {
        inputHtml = `<textarea class="form-control form-control-sm" rows="4">${currentValue}</textarea>`;
    } else if (fieldType === 'number') {
        inputHtml = `<input type="number" class="form-control form-control-sm" value="${currentValue}" min="0" max="999">`;
    } else {
        inputHtml = `<input type="text" class="form-control form-control-sm" value="${currentValue}">`;
    }

    const editContainer = document.createElement('div');
    editContainer.className = 'tdr-edit-field';
    editContainer.innerHTML = `
        <div class="tdr-edit-input" style="margin-bottom:8px;">${inputHtml}</div>
        <div class="tdr-edit-actions" style="display:flex;gap:8px;">
            <button class="btn btn-primary btn-sm"   onclick="saveField(this, ${ticketId}, '${fieldName}')">Save</button>
            <button class="btn btn-secondary btn-sm" onclick="cancelEdit(this)">Cancel</button>
        </div>
    `;

    // Find target container to replace
    let targetElement;
    if (fieldName === 'title') {
        targetElement = document.querySelector('.tdr-title-container');
    } else if (fieldName === 'description') {
        targetElement = document.querySelector('.tdr-description').parentNode;
    } else if (fieldName === 'status') {
        targetElement = element.closest('.tdr-status-container') || element.parentNode;
    } else {
        targetElement = element.closest('.tdr-meta-item') || element.parentNode;
    }

    targetElement.dataset.original = targetElement.innerHTML;
    targetElement.innerHTML = '';
    targetElement.appendChild(editContainer);

    // Auto-focus
    const input = editContainer.querySelector('input, select, textarea');
    if (input) input.focus();
}

// ─── Save via inline-update endpoint ───────────────────────────────────────
function saveField(button, ticketId, fieldName) {
    const editContainer = button.closest('.tdr-edit-field');
    const input         = editContainer.querySelector('input, select, textarea');
    const value         = input ? input.value : '';
    const projectId     = document.getElementById('tdrInner').dataset.projectId;

    fetch(`/projects/${projectId}/ticket/${ticketId}/inline-update/`, {
        method: 'POST',
        headers: {
            'Content-Type':     'application/x-www-form-urlencoded',
            'X-CSRFToken':      getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: new URLSearchParams({ field: fieldName, value: value })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            openTicketDrawer(ticketId, `/projects/${projectId}/ticket/detail/${ticketId}/?drawer=1`);
        } else {
            alert('Error: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(err => {
        console.error(err);
        alert('Network error: ' + err.message);
    });
}

function cancelEdit(button) {
    const editContainer = button.closest('.tdr-edit-field');
    const parent        = editContainer.parentNode;
    parent.innerHTML    = parent.dataset.original || '';
}

// ─── Assignee (fetch project members) ──────────────────────────────────────
function fetchAssignees(projectId, ticketId, element) {
    const targetElement = element.closest('.tdr-meta-item') || element.parentNode;
    const originalContent = targetElement.innerHTML;
    targetElement.dataset.original = originalContent;

    targetElement.innerHTML = `
        <div class="tdr-edit-field">
            <div class="tdr-edit-input" style="margin-bottom:8px;">
                <select class="form-control form-control-sm" id="assigneeSelect">
                    <option value="">— Unassigned —</option>
                    <option value="loading" disabled>Loading members...</option>
                </select>
            </div>
            <div style="display:flex;gap:8px;">
                <button class="btn btn-primary btn-sm"
                    onclick="saveField(this, ${ticketId}, 'assignee_id')">Save</button>
                <button class="btn btn-secondary btn-sm" onclick="cancelEdit(this)">Cancel</button>
            </div>
        </div>
    `;

    // Load members via API with better error handling
    fetch(`/projects/${projectId}/members-json/`, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(r => {
        if (!r.ok) {
            throw new Error(`HTTP error! status: ${r.status}`);
        }
        return r.json();
    })
    .then(data => {
        const select = document.getElementById('assigneeSelect');
        if (select) {
            // Clear loading option
            select.innerHTML = '<option value="">— Unassigned —</option>';

            if (data.members && data.members.length > 0) {
                data.members.forEach(m => {
                    const opt = document.createElement('option');
                    opt.value = m.id;
                    opt.textContent = m.name;
                    select.appendChild(opt);
                });
            } else {
                // If no members, show message
                const opt = document.createElement('option');
                opt.value = "";
                opt.disabled = true;
                opt.textContent = "No members available";
                select.appendChild(opt);
            }
        }
    })
    .catch(error => {
        console.error('Error loading members:', error);
        const select = document.getElementById('assigneeSelect');
        if (select) {
            select.innerHTML = '<option value="">— Unassigned —</option>';
            const opt = document.createElement('option');
            opt.value = "";
            opt.disabled = true;
            opt.textContent = "Error loading members";
            select.appendChild(opt);
        }
    });
}
// ─── CSRF cookie helper ─────────────────────────────────────────────────────
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        for (const cookie of document.cookie.split(';')) {
            const c = cookie.trim();
            if (c.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(c.slice(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
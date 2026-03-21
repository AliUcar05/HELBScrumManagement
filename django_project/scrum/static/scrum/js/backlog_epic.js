// backlog_epic.js
// All backlog page JS: epic panel, sprint modals, move-to-sprint, sprint goal prompt

var EPIC_PALETTE = [
    '#0052cc', '#ff8b00', '#6554c0', '#00875a',
    '#de350b', '#00b8d9', '#36b37e', '#ff5630'
];

document.addEventListener('DOMContentLoaded', function () {

    // --- Apply colors to epic items in panel ---
    document.querySelectorAll('.epic-item').forEach(function (item) {
        var idx   = parseInt(item.dataset.epicIndex || '0', 10) % EPIC_PALETTE.length;
        var color = EPIC_PALETTE[idx];
        item.style.setProperty('--epic-color', color);
        var pk   = item.id.replace('epic-item-', '');
        var fill = document.getElementById('epic-fill-' + pk);
        if (fill) fill.style.background = color;
    });

    // --- Color the active filter banner ---
    var banner = document.querySelector('.epic-filter-banner');
    if (banner) {
        var idx   = parseInt(banner.dataset.epicIndex || '0', 10) % EPIC_PALETTE.length;
        var color = EPIC_PALETTE[idx];
        banner.style.setProperty('--epic-color', color);
        banner.style.borderLeftColor = color;
        banner.style.background = color + '18';
    }

    // --- Close all epic dropdowns on outside click ---
    document.addEventListener('click', function () {
        closeAllEpicMenus();
    });

    // --- Sprint goal prompt buttons ---
    var noGoalBtn = document.getElementById('startWithoutGoalBtn');
    if (noGoalBtn) {
        noGoalBtn.addEventListener('click', function () {
            $('#sprintGoalPromptModal').modal('hide');
            submitStartSprint(window._pendingStartUrl, null);
        });
    }
    var withGoalBtn = document.getElementById('startWithGoalBtn');
    if (withGoalBtn) {
        withGoalBtn.addEventListener('click', function () {
            var goal = document.getElementById('goalPromptInput').value.trim();
            $('#sprintGoalPromptModal').modal('hide');
            submitStartSprint(window._pendingStartUrl, goal);
        });
    }

    // --- Preselect epic in create modal if filter_epic is active ---
    var createBtn = document.getElementById('createIssueBtn');
    if (createBtn && createBtn.dataset.epicId) {
        createBtn.addEventListener('click', function () {
            setTimeout(function () {
                if (typeof preselectEpicInModal === 'function') {
                    preselectEpicInModal(createBtn.dataset.epicId, createBtn.dataset.epicTitle || '');
                }
            }, 250);
        });
    }
});

// ── Epic panel open/close ─────────────────────────────────────
function toggleEpicPanel() {
    document.getElementById('epicPanel').classList.toggle('open');
    document.getElementById('epicTabLabel').classList.toggle('active');
}

// ── Epic item click: expand stats OR navigate to filter ───────
function handleEpicClick(event, epicPk, filterUrl) {
    if (event.target.closest('.epic-item-menu-btn')) return;
    if (event.target.closest('.epic-item-dropdown')) return;

    var body    = document.getElementById('epic-body-' + epicPk);
    var chevron = document.getElementById('epic-chev-' + epicPk);
    if (!body) return;

    if (body.classList.contains('open')) {
        body.classList.remove('open');
        if (chevron) chevron.classList.remove('open');
    } else {
        body.classList.add('open');
        if (chevron) chevron.classList.add('open');
        window.location.href = filterUrl;
    }
}

// ── Epic three-dot menu ───────────────────────────────────────
function toggleEpicMenu(event, epicPk) {
    event.stopPropagation();
    var menu = document.getElementById('epic-menu-' + epicPk);
    if (!menu) return;
    var isOpen = menu.classList.contains('open');
    closeAllEpicMenus();
    if (!isOpen) menu.classList.add('open');
}

function closeAllEpicMenus() {
    document.querySelectorAll('.epic-item-dropdown.open').forEach(function (m) {
        m.classList.remove('open');
    });
}

// ── Open create modal preselected for an epic ─────────────────
function openCreateInEpicModal(epicId, epicTitle) {
    $('#globalCreateTicketModal').modal('show');
    setTimeout(function () {
        if (typeof preselectEpicInModal === 'function') {
            preselectEpicInModal(epicId, epicTitle);
        }
    }, 250);
}

// ── Open create modal with Epic type preselected ──────────────
function openCreateModalAsEpic() {
    $('#globalCreateTicketModal').modal('show');
    setTimeout(function () {
        var el = document.querySelector('#typeSelectorModal .type-option[data-value="epic"]');
        if (el && typeof selectTicketType === 'function') {
            selectTicketType(el);
        }
    }, 200);
}

// ── Edit Sprint modal ─────────────────────────────────────────
function openEditSprintModal(sprintPk, name, goals, startDate, endDate, capacity) {
    document.getElementById('editSprintName').value     = name      || '';
    document.getElementById('editSprintGoal').value     = goals     || '';
    document.getElementById('editSprintStart').value    = startDate || '';
    document.getElementById('editSprintEnd').value      = endDate   || '';
    document.getElementById('editSprintCapacity').value = (capacity !== null && capacity !== undefined && capacity !== 'null') ? capacity : '';
    document.getElementById('editSprintForm').action    = '/projects/' + PROJECT_PK + '/sprints/' + sprintPk + '/update/';
    $('#editSprintModal').modal('show');
}

// ── Sprint start with optional goal prompt ────────────────────
function handleStartSprint(sprintPk, currentGoal, startUrl) {
    if (currentGoal && currentGoal.trim()) {
        submitStartSprint(startUrl, null);
    } else {
        window._pendingStartUrl = startUrl;
        document.getElementById('goalPromptInput').value = '';
        $('#sprintGoalPromptModal').modal('show');
    }
}

function submitStartSprint(url, goal) {
    var form = document.createElement('form');
    form.method = 'POST';
    form.action = url;
    addHidden(form, 'csrfmiddlewaretoken', CSRF_TOKEN);
    if (goal) addHidden(form, 'goal_override', goal);
    document.body.appendChild(form);
    form.submit();
}

// ── Move to Sprint ────────────────────────────────────────────
function openMoveToSprintModal(ticketId, ticketLabel) {
    document.getElementById('mts-ticket-id').value = ticketId;
    document.getElementById('mts-ticket-label').textContent = 'Move "' + ticketLabel + '" to:';
    $('#moveToSprintModal').modal('show');
}

function doMoveToSprint(ticketId, sprintId) {
    $('#moveToSprintModal').modal('hide');
    formPost('/projects/' + PROJECT_PK + '/ticket/move-to-sprint/', {
        ticket_id: ticketId,
        sprint_id: sprintId
    });
}

function doRemoveFromSprint(ticketId) {
    if (!confirm('Move this ticket back to the backlog?')) return;
    formPost('/projects/' + PROJECT_PK + '/ticket/remove-from-sprint/', {
        ticket_id: ticketId
    });
}

// ── Helpers ───────────────────────────────────────────────────
function addHidden(form, name, value) {
    var input = document.createElement('input');
    input.type  = 'hidden';
    input.name  = name;
    input.value = value;
    form.appendChild(input);
}

function formPost(url, fields) {
    var form = document.createElement('form');
    form.method = 'POST';
    form.action = url;
    addHidden(form, 'csrfmiddlewaretoken', CSRF_TOKEN);
    Object.keys(fields).forEach(function (k) {
        addHidden(form, k, fields[k]);
    });
    document.body.appendChild(form);
    form.submit();
}
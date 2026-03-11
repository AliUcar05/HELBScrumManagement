// Édition inline dans le drawer
function editField(fieldName) {
    const ticketId = document.getElementById('tdrInner').dataset.ticketId;
    const projectId = document.getElementById('tdrInner').dataset.projectId;
    const element = event.target.closest('[onclick^="editField"]') || event.target;

    // Récupérer la valeur actuelle
    let currentValue = '';
    let fieldType = 'text';
    let options = [];

    switch(fieldName) {
        case 'title':
            currentValue = document.getElementById('tdrTitle').textContent;
            break;
        case 'description':
            currentValue = document.getElementById('tdrDescription').innerText;
            fieldType = 'textarea';
            break;
        case 'priority':
            currentValue = element.classList.contains('priority')
                ? element.className.match(/priority-(\w+)/)[1]
                : 'medium';
            fieldType = 'select';
            options = [
                { value: 'highest', label: 'Highest' },
                { value: 'high', label: 'High' },
                { value: 'medium', label: 'Medium' },
                { value: 'low', label: 'Low' }
            ];
            break;
        case 'status':
            currentValue = element.classList.contains('tdr-status')
                ? element.className.match(/status-(\w+)/)[1]
                : 'todo';
            fieldType = 'select';
            options = [
                { value: 'todo', label: 'To Do' },
                { value: 'in_progress', label: 'In Progress' },
                { value: 'done', label: 'Done' }
            ];
            break;
        case 'story_points':
            currentValue = element.querySelector('.tdr-points').textContent;
            if (currentValue === '—') currentValue = '';
            fieldType = 'number';
            break;
        case 'assignee':
            fieldType = 'select';
            // Charger les assignees via AJAX
            fetchAssignees(projectId, ticketId);
            return;
    }

    // Créer le formulaire d'édition
    const editContainer = document.createElement('div');
    editContainer.className = 'tdr-edit-field';

    let inputHtml = '';
    if (fieldType === 'select') {
        inputHtml = '<select class="form-control">';
        options.forEach(opt => {
            const selected = opt.value === currentValue ? 'selected' : '';
            inputHtml += `<option value="${opt.value}" ${selected}>${opt.label}</option>`;
        });
        inputHtml += '</select>';
    } else if (fieldType === 'textarea') {
        inputHtml = `<textarea class="form-control" rows="4">${currentValue}</textarea>`;
    } else if (fieldType === 'number') {
        inputHtml = `<input type="number" class="form-control" value="${currentValue}" min="0" max="100">`;
    } else {
        inputHtml = `<input type="text" class="form-control" value="${currentValue}">`;
    }

    editContainer.innerHTML = `
        <div class="tdr-edit-input">${inputHtml}</div>
        <div class="tdr-edit-actions">
            <button class="btn btn-primary btn-sm" onclick="saveField(this, ${ticketId}, '${fieldName}')">Save</button>
            <button class="btn btn-secondary btn-sm" onclick="cancelEdit(this)">Cancel</button>
        </div>
    `;

    // Remplacer le contenu
    const targetElement = fieldName === 'title'
        ? document.querySelector('.tdr-title-container')
        : fieldName === 'description'
            ? document.querySelector('.tdr-description').parentNode
            : element.closest('.tdr-meta-item') || element.closest('.tdr-status-container') || element.parentNode;

    const originalContent = targetElement.innerHTML;
    targetElement.dataset.original = originalContent;
    targetElement.innerHTML = '';
    targetElement.appendChild(editContainer);
}

function saveField(button, ticketId, fieldName) {
    const editContainer = button.closest('.tdr-edit-field');
    const input = editContainer.querySelector('input, select, textarea');
    const value = input.value;
    const projectId = document.getElementById('tdrInner').dataset.projectId;

    fetch(`/projects/${projectId}/ticket/update/${ticketId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: new URLSearchParams({
            [fieldName]: value
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Recharger le drawer
            openTicketDrawer(ticketId, `/projects/${projectId}/ticket/detail/${ticketId}/?drawer=1`);
        } else {
            alert('Error saving field');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error saving field');
    });
}

function cancelEdit(button) {
    const editContainer = button.closest('.tdr-edit-field');
    const parent = editContainer.parentNode;
    parent.innerHTML = parent.dataset.original || '';
}

function fetchAssignees(projectId, ticketId) {
    // Implémenter le chargement des assignees
    console.log('Fetch assignees for project', projectId);
}

function addComment(ticketId) {
    const commentText = document.getElementById('newComment').value;
    if (!commentText.trim()) return;

    const projectId = document.getElementById('tdrInner').dataset.projectId;

    fetch(`/projects/${projectId}/ticket/${ticketId}/comment/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: new URLSearchParams({
            content: commentText
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById('newComment').value = '';
            openTicketDrawer(ticketId, `/projects/${projectId}/ticket/detail/${ticketId}/?drawer=1`);
        }
    })
    .catch(error => console.error('Error:', error));
}

// Fonction pour récupérer le cookie CSRF
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
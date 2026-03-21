function toggleSprint(sprintId) {
    var body    = document.getElementById('spt-body-' + sprintId);
    var subinfo = document.getElementById('subinfo-' + sprintId);
    var chevron = document.getElementById('chevron-' + sprintId);

    if (!body) return;

    var isCollapsed = body.classList.contains('collapsed');

    if (isCollapsed) {
        body.classList.remove('collapsed');
        if (subinfo) subinfo.classList.remove('collapsed');
        chevron.classList.remove('collapsed');
    } else {
        body.classList.add('collapsed');
        if (subinfo) subinfo.classList.add('collapsed');
        chevron.classList.add('collapsed');
    }
}

function toggleSprintMenu(event, sprintId) {
    event.stopPropagation();

    document.querySelectorAll('.spt-dropdown').forEach(function(d) {
        if (d.id !== 'sprint-menu-' + sprintId) {
            d.classList.remove('open');
        }
    });

    var menu = document.getElementById('sprint-menu-' + sprintId);
    if (menu) menu.classList.toggle('open');
}

document.addEventListener('click', function() {
    document.querySelectorAll('.spt-dropdown').forEach(function(d) {
        d.classList.remove('open');
    });
});
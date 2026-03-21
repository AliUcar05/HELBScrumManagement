function handleDurationChange(sel) {
    var weeks = parseInt(sel.value, 10);
    if (isNaN(weeks)) return;

    var startInput = document.getElementById('sprintStartDate');
    if (!startInput.value) return;

    var start = new Date(startInput.value);
    var end = new Date(start);
    end.setDate(end.getDate() + weeks * 7 - 1);
    document.getElementById('sprintEndDate').value = end.toISOString().split('T')[0];
}

function handleStartDateChange() {
    var sel = document.getElementById('sprintDuration');
    if (sel.value !== 'custom') handleDurationChange(sel);
}

function syncDurationFromDates() {
    document.getElementById('sprintDuration').value = 'custom';
}

document.addEventListener('DOMContentLoaded', function () {
    var modal = document.getElementById('createSprintModal');
    if (!modal) return;

    $(modal).on('show.bs.modal', function () {
        var form = document.getElementById('createSprintForm');
        if (form) form.reset();
    });
});
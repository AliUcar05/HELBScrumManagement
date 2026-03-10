(function () {
  'use strict';

  const modal       = document.getElementById('globalCreateTicketModal');
  const form        = document.getElementById('gctForm');
  const projectSel  = document.getElementById('gct_project');
  const titleInput  = document.getElementById('gct_title');
  const titleErr    = document.getElementById('gct_title_err');
  const projectErr  = document.getElementById('gct_project_err');
  const assigneeSel = document.getElementById('gct_assignee');
  const submitBtn   = document.getElementById('gctSubmitBtn');
  const btnLabel    = submitBtn.querySelector('.gct-btn-label');
  const btnSpinner  = submitBtn.querySelector('.gct-btn-spinner');
  const successBanner = document.getElementById('gctSuccessBanner');
  const successText   = document.getElementById('gctSuccessText');
  const successLink   = document.getElementById('gctSuccessLink');

  // ── Enable submit only when a project is selected ────────────────────────
  function syncSubmitState() {
    submitBtn.disabled = !projectSel.value;
  }
  projectSel.addEventListener('change', syncSubmitState);
  syncSubmitState();

  // ── When project changes, reload assignee options via AJAX ────────────────
  projectSel.addEventListener('change', function () {
    const pk = this.value;
    assigneeSel.innerHTML = '<option value="">— Unassigned —</option>';
    if (!pk) return;

    fetch('/api/projects/' + pk + '/members/', {
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(r => r.ok ? r.json() : null)
    .then(data => {
      if (!data) return;
      data.forEach(function (m) {
        const opt = document.createElement('option');
        opt.value = m.id;
        opt.textContent = m.full_name || m.username;
        assigneeSel.appendChild(opt);
      });
    })
    .catch(() => {}); // silently fail — assignee stays empty
  });

  // ── Reset form when modal opens ───────────────────────────────────────────
  $(modal).on('show.bs.modal', function () {
    form.reset();
    successBanner.style.display = 'none';
    clearErrors();
    syncSubmitState();
  });

  // ── Helpers ───────────────────────────────────────────────────────────────
  function clearErrors() {
    [titleInput].forEach(function (el) {
      el.classList.remove('is-invalid');
    });
    titleErr.textContent = '';
    projectErr.textContent = '';
  }

  function setLoading(on) {
    submitBtn.disabled = on;
    btnLabel.style.display   = on ? 'none'  : 'inline';
    btnSpinner.style.display = on ? 'flex'  : 'none';
  }

  function showSuccess(title, detailUrl) {
    successText.textContent = '"' + title + '" created successfully!';
    if (detailUrl) {
      successLink.href = detailUrl;
      successLink.style.display = '';
    } else {
      successLink.style.display = 'none';
    }
    successBanner.style.display = 'flex';

    // Reset the form fields but keep the modal open
    form.reset();
    syncSubmitState();

    // Auto-hide banner after 6 s
    setTimeout(function () {
      successBanner.style.display = 'none';
    }, 6000);
  }

  function showFieldErrors(errors) {
    Object.entries(errors).forEach(function ([field, errs]) {
      const msg = Array.isArray(errs) ? errs[0] : errs;
      if (field === 'title') {
        titleInput.classList.add('is-invalid');
        titleErr.textContent = msg;
      } else {
        // Generic fallback — alert for unexpected fields
        console.warn('Form error on field "' + field + '":', msg);
      }
    });
  }

  // ── Submit ────────────────────────────────────────────────────────────────
  form.addEventListener('submit', function (e) {
    e.preventDefault();
    clearErrors();

    // Client-side validation
    let valid = true;
    if (!projectSel.value) {
      projectSel.classList.add('is-invalid');
      projectErr.textContent = 'Please select a project.';
      valid = false;
    }
    if (!titleInput.value.trim()) {
      titleInput.classList.add('is-invalid');
      titleErr.textContent = 'Title is required.';
      valid = false;
    }
    if (!valid) return;

    // Determine POST URL from the selected option's data attribute
    const selectedOption = projectSel.options[projectSel.selectedIndex];
    const postUrl = selectedOption.dataset.createUrl;
    if (!postUrl) {
      projectErr.textContent = 'Cannot determine URL for this project.';
      return;
    }

    setLoading(true);

    const formData = new FormData(form);
    // Remove the UI-only _project field (not expected by the view)
    formData.delete('_project');

    fetch(postUrl, {
      method: 'POST',
      body: formData,
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(function (r) { return r.json(); })
    .then(function (json) {
      setLoading(false);
      if (json.success) {
        // Build detail URL if the view returns ticket_id
        let detailUrl = null;
        if (json.ticket_id) {
          const pk = projectSel.value;
          detailUrl = '/projects/' + pk + '/ticket/detail/' + json.ticket_id + '/';
        }
        showSuccess(titleInput.value, detailUrl);
      } else {
        if (json.errors) { showFieldErrors(json.errors); }
        else { alert('Something went wrong. Please try again.'); }
      }
    })
    .catch(function () {
      setLoading(false);
      alert('Network error. Please check your connection and try again.');
    });
  });

})();
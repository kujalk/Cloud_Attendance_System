/* Cloud Attendance System — Main JS */

document.addEventListener('DOMContentLoaded', () => {

  // ─── Sidebar Toggle (mobile) ──────────────────────────────────────────────
  const sidebar  = document.getElementById('sidebar');
  const overlay  = document.getElementById('sidebarOverlay');
  const toggleBtn = document.getElementById('sidebarToggle');

  function openSidebar()  { sidebar?.classList.add('open');   overlay?.classList.add('active'); }
  function closeSidebar() { sidebar?.classList.remove('open'); overlay?.classList.remove('active'); }

  toggleBtn?.addEventListener('click', openSidebar);
  overlay?.addEventListener('click', closeSidebar);

  // ─── Auto-dismiss Django messages as toasts ───────────────────────────────
  document.querySelectorAll('.django-message').forEach(el => {
    setTimeout(() => el.remove(), 5000);
  });

  // ─── Animated counters ───────────────────────────────────────────────────
  document.querySelectorAll('.count-up').forEach(el => {
    const target = parseInt(el.dataset.target || el.textContent, 10);
    if (isNaN(target)) return;
    const duration = 900;
    const step = Math.ceil(duration / target) || 1;
    let current = 0;
    el.textContent = '0';
    const timer = setInterval(() => {
      current = Math.min(current + Math.ceil(target / 40), target);
      el.textContent = current.toLocaleString();
      if (current >= target) clearInterval(timer);
    }, step);
  });

  // ─── Attendance Mark — status toggle buttons ──────────────────────────────
  document.querySelectorAll('.status-group').forEach(group => {
    const hiddenInput = group.querySelector('input[type="hidden"]');
    const buttons     = group.querySelectorAll('.s-btn');

    buttons.forEach(btn => {
      btn.addEventListener('click', () => {
        const val = btn.dataset.value;
        buttons.forEach(b => {
          b.classList.remove('active-present','active-absent','active-late','active-excused');
        });
        btn.classList.add(`active-${val.toLowerCase()}`);
        if (hiddenInput) hiddenInput.value = val;
      });

      // Apply initial state from existing data
      const cur = hiddenInput?.value;
      if (cur && btn.dataset.value === cur) {
        btn.classList.add(`active-${cur.toLowerCase()}`);
      }
    });
  });

  // ─── Mark all present / absent helpers ───────────────────────────────────
  window.markAll = (status) => {
    document.querySelectorAll('.status-group').forEach(group => {
      const hiddenInput = group.querySelector('input[type="hidden"]');
      const buttons     = group.querySelectorAll('.s-btn');
      buttons.forEach(b => {
        b.classList.remove('active-present','active-absent','active-late','active-excused');
        if (b.dataset.value === status) b.classList.add(`active-${status.toLowerCase()}`);
      });
      if (hiddenInput) hiddenInput.value = status;
    });
  };

  // ─── Table search (client-side) ───────────────────────────────────────────
  const tableSearch = document.getElementById('tableSearch');
  if (tableSearch) {
    tableSearch.addEventListener('input', () => {
      const q = tableSearch.value.toLowerCase();
      document.querySelectorAll('.searchable-table tbody tr').forEach(row => {
        row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
      });
    });
  }

  // ─── Form validation highlight ────────────────────────────────────────────
  document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', () => {
      form.querySelectorAll('[required]').forEach(field => {
        if (!field.value.trim()) {
          field.style.borderColor = 'var(--danger)';
        }
      });
    });
  });

  // ─── Delete confirmation ──────────────────────────────────────────────────
  document.querySelectorAll('[data-confirm]').forEach(el => {
    el.addEventListener('click', e => {
      if (!confirm(el.dataset.confirm || 'Are you sure?')) {
        e.preventDefault();
      }
    });
  });

  // ─── Tooltip init (Bootstrap) ────────────────────────────────────────────
  const tooltipEls = document.querySelectorAll('[data-bs-toggle="tooltip"]');
  if (typeof bootstrap !== 'undefined') {
    tooltipEls.forEach(el => new bootstrap.Tooltip(el));
  }

  // ─── Subject filter → reload with date param ─────────────────────────────
  const subjectFilter = document.getElementById('subjectFilter');
  const dateFilter    = document.getElementById('dateFilter');

  if (subjectFilter && dateFilter) {
    [subjectFilter, dateFilter].forEach(el => {
      el.addEventListener('change', () => {
        const subject = subjectFilter.value;
        const date    = dateFilter.value || new Date().toISOString().slice(0,10);
        if (subject) {
          window.location.href = `?subject=${subject}&date=${date}`;
        }
      });
    });
  }

});

// ─── Toast helper (callable from templates) ──────────────────────────────────
window.showToast = (message, type = 'info') => {
  const container = document.getElementById('toastContainer')
    || (() => {
      const c = document.createElement('div');
      c.id = 'toastContainer';
      c.className = 'toast-container';
      document.body.appendChild(c);
      return c;
    })();

  const icons = { success: 'fa-check-circle', error: 'fa-exclamation-circle', info: 'fa-info-circle' };
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<i class="fas ${icons[type] || icons.info}"></i><span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => { toast.style.opacity = '0'; setTimeout(() => toast.remove(), 300); }, 4000);
};

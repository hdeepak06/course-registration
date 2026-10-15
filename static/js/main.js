/**
 * CourseConnect — Client-side Interactivity & Modal Handling
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Mobile Navigation Toggle
  const mobileToggle = document.getElementById('mobileToggle');
  const navLinks = document.getElementById('navLinks');

  if (mobileToggle && navLinks) {
    mobileToggle.addEventListener('click', () => {
      navLinks.classList.toggle('active');
      const isExpanded = navLinks.classList.contains('active');
      mobileToggle.setAttribute('aria-expanded', isExpanded);
    });
  }

  // 2. Alert Dismissal
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(alert => {
    const closeBtn = alert.querySelector('.alert-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => {
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-8px)';
        setTimeout(() => alert.remove(), 250);
      });
    }

    // Auto-dismiss after 6 seconds
    setTimeout(() => {
      if (document.body.contains(alert)) {
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-8px)';
        setTimeout(() => alert.remove(), 250);
      }
    }, 6000);
  });

  // 3. Modal System
  const modalBackdrops = document.querySelectorAll('.modal-backdrop');
  
  function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.add('active');
      document.body.style.overflow = 'hidden';
    }
  }

  function closeModal(modal) {
    if (modal) {
      modal.classList.remove('active');
      document.body.style.overflow = '';
    }
  }

  // Modal triggers
  document.querySelectorAll('[data-modal-target]').forEach(trigger => {
    trigger.addEventListener('click', (e) => {
      e.preventDefault();
      const targetId = trigger.getAttribute('data-modal-target');
      openModal(targetId);
    });
  });

  // Close triggers
  document.querySelectorAll('[data-modal-close]').forEach(closeBtn => {
    closeBtn.addEventListener('click', () => {
      const modal = closeBtn.closest('.modal-backdrop');
      closeModal(modal);
    });
  });

  // Click outside modal dialog to dismiss
  modalBackdrops.forEach(backdrop => {
    backdrop.addEventListener('click', (e) => {
      if (e.target === backdrop) {
        closeModal(backdrop);
      }
    });
  });

  // ESC key to close active modal
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      const activeModal = document.querySelector('.modal-backdrop.active');
      if (activeModal) {
        closeModal(activeModal);
      }
    }
  });

  // 4. Quick Details Preview Modal via API
  const quickDetailButtons = document.querySelectorAll('.btn-quick-detail');
  const detailModal = document.getElementById('courseDetailModal');

  if (detailModal && quickDetailButtons.length > 0) {
    quickDetailButtons.forEach(btn => {
      btn.addEventListener('click', async (e) => {
        e.preventDefault();
        const courseId = btn.getAttribute('data-course-id');
        
        const modalTitle = detailModal.querySelector('.modal-title');
        const modalBody = detailModal.querySelector('.modal-body');
        const modalEnrollLink = detailModal.querySelector('#modalEnrollBtn');

        modalTitle.textContent = "Loading Course Details...";
        modalBody.innerHTML = `<div style="text-align: center; padding: 2rem;"><p>Fetching latest course information...</p></div>`;
        openModal('courseDetailModal');

        try {
          const res = await fetch(`/api/courses/${courseId}`);
          const data = await res.json();
          if (data.status === 'success') {
            const c = data.course;
            modalTitle.textContent = `${c.course_code}: ${c.course_title}`;
            modalBody.innerHTML = `
              <div style="margin-bottom: 1rem;">
                <span class="course-dept-tag">${c.department}</span>
                <span style="margin-left: 0.5rem; font-size: 0.85rem; color: var(--text-muted);">${c.credits} Credits</span>
              </div>
              <p style="margin-bottom: 1rem; line-height: 1.6; color: var(--text-main);">${c.description}</p>
              <div class="course-meta-bar" style="margin-bottom: 1rem;">
                <div class="meta-row">
                  <span class="meta-label">Instructor:</span>
                  <span class="meta-value">${c.instructor}</span>
                </div>
                <div class="meta-row">
                  <span class="meta-label">Available Seats:</span>
                  <span class="meta-value ${c.available_seats === 0 ? 'text-danger' : ''}">${c.available_seats} of ${c.max_seats}</span>
                </div>
              </div>
            `;

            if (modalEnrollLink) {
              const enrollForm = detailModal.querySelector('#modalEnrollForm');
              if (enrollForm) {
                enrollForm.action = `/courses/${c.course_id}/enroll`;
              }
              if (c.available_seats === 0) {
                modalEnrollLink.textContent = "Course Full";
                modalEnrollLink.classList.add('btn-disabled');
                modalEnrollLink.disabled = true;
              } else {
                modalEnrollLink.textContent = "Confirm Registration";
                modalEnrollLink.classList.remove('btn-disabled');
                modalEnrollLink.disabled = false;
              }
            }
          } else {
            modalBody.innerHTML = `<p class="text-danger">Unable to load details.</p>`;
          }
        } catch (err) {
          modalBody.innerHTML = `<p class="text-danger">Network error loading course details.</p>`;
        }
      });
    });
  }

  // 5. Delete Course Confirmation Setup
  const deleteButtons = document.querySelectorAll('.btn-trigger-delete');
  const deleteModal = document.getElementById('deleteConfirmModal');
  const deleteForm = document.getElementById('deleteCourseForm');
  const deleteCourseName = document.getElementById('deleteCourseName');

  if (deleteButtons.length > 0 && deleteModal && deleteForm) {
    deleteButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        const courseId = btn.getAttribute('data-course-id');
        const courseCode = btn.getAttribute('data-course-code');
        const courseTitle = btn.getAttribute('data-course-title');

        deleteCourseName.textContent = `${courseCode} - ${courseTitle}`;
        deleteForm.action = `/admin/courses/${courseId}/delete`;
        openModal('deleteConfirmModal');
      });
    });
  }
});

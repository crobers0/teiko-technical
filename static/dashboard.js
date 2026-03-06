document.addEventListener('DOMContentLoaded', function () {
  // Visuals: switch iframe src when clicking buttons
  const vizButtons = document.querySelectorAll('.viz-btn');
  const vizFrame = document.getElementById('viz-frame');
  if (vizButtons && vizFrame) {
    vizButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        vizButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const src = btn.getAttribute('data-src');
        if (src) vizFrame.src = src;
      });
    });
    // mark first active
    if (vizButtons[0]) vizButtons[0].classList.add('active');
  }

  // Analytics: simple refresh (reload page)
  const refreshBtn = document.getElementById('refresh-stats');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', () => {
      // just reload the page to fetch updated CSV if available
      location.reload();
    });
  }
});

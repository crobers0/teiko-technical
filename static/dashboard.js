document.addEventListener('DOMContentLoaded', function () {
  // Highlight current nav button based on current URL
  const currentPath = window.location.pathname;
  const navLinks = document.querySelectorAll('.nav-link');
  navLinks.forEach(link => {
    const href = link.getAttribute('href');
    if (href === currentPath) {
      link.classList.add('active');
    } else {
      link.classList.remove('active');
    }
  });

  // Handle viz button tab switching for data-table and summary-stats
  const vizButtons = document.querySelectorAll('.viz-btn');
  if (vizButtons.length > 0) {
    vizButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        const targetView = btn.getAttribute('data-view');
        
        // Hide all view containers
        const dataTableContainer = document.getElementById('data-table-container');
        const summaryStatsContainer = document.getElementById('summary-stats-container');
        
        if (dataTableContainer) dataTableContainer.style.display = 'none';
        if (summaryStatsContainer) summaryStatsContainer.style.display = 'none';
        
        // Show the target container
        if (targetView === 'data-table' && dataTableContainer) {
          dataTableContainer.style.display = 'block';
        } else if (targetView === 'summary-stats' && summaryStatsContainer) {
          summaryStatsContainer.style.display = 'block';
        }
        
        // Update active button state
        vizButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
      });
    });
    
    // Set first button as active on page load
    if (vizButtons[0]) {
      vizButtons[0].classList.add('active');
    }
  }
  
  // switch iframe src when clicking buttons (for visualization pages)
  const vizFrame = document.getElementById('viz-frame');
  if (vizFrame) {
    const vizButtonsIframe = document.querySelectorAll('.viz-btn');
    vizButtonsIframe.forEach(btn => {
      btn.addEventListener('click', () => {
        const src = btn.getAttribute('data-src');
        if (src) vizFrame.src = src;
      });
    });
  }

  // adjust iframe content to avoid horizontal scrolling and make plots responsive
  function injectResponsiveStyles(iframe) {
    try {
      const doc = iframe.contentDocument || iframe.contentWindow.document;
      if (!doc) return;

      // add stylesheet to enforce max-width behavior
      const styleId = 'injected-responsive-styles';
      if (!doc.getElementById(styleId)) {
        const style = doc.createElement('style');
        style.id = styleId;
        style.innerHTML = `html,body{height:100%;margin:0;overflow:hidden}*{box-sizing:border-box;max-width:100%}img,svg,iframe,table{max-width:100%!important;height:auto!important}div.plotly, .plotly-svg{max-width:100%!important;width:100%!important}body > *{max-width:100%}`;
        doc.head && doc.head.appendChild(style);
      }

      // try to resize any Plotly charts inside the iframe
      const resizePlots = () => {
        const plots = doc.querySelectorAll('.plotly, .js-plotly-plot');
        if (!plots || plots.length === 0) return;
        // prefer Plotly from iframe if available, otherwise use parent Plotly
        const P = (iframe.contentWindow && iframe.contentWindow.Plotly) || window.Plotly;
        plots.forEach(p => {
          try {
            p.style.width = '100%';
            if (P && P.Plots && typeof P.Plots.resize === 'function') {
              P.Plots.resize(p);
            } else if (P && typeof P.relayout === 'function') {
              P.relayout(p, {autosize: true});
            }
          } catch (e) {
            // ignore individual plot errors
          }
        });
      };

      // run once after a short delay to allow content markers to render
      setTimeout(resizePlots, 150);
      // also run a bit later for slow renders
      setTimeout(resizePlots, 800);
    } catch (err) {
      // cross-origin or other access error — nothing to do
    }
  }

  // attach load handler and window resize to keep iframe content responsive
  if (vizFrame) {
    vizFrame.addEventListener('load', () => injectResponsiveStyles(vizFrame));
    let resizeTimer = null;
    window.addEventListener('resize', () => {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(() => injectResponsiveStyles(vizFrame), 200);
    });
  }

  // simple refresh (reload page)
  const refreshBtn = document.getElementById('refresh-stats');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', () => {
      // reload the page to fetch updated CSV if available
      location.reload();
    });
  }

});

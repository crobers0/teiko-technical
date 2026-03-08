document.addEventListener('DOMContentLoaded', function () {
  // switch iframe src when clicking buttons
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

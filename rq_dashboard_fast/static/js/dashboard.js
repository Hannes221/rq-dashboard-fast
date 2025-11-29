(function (window, document) {
  const notificationDuration = 3000;

  function dismissAfterDelay(element) {
    setTimeout(() => {
      if (element && element.parentNode) {
        element.parentNode.removeChild(element);
      }
    }, notificationDuration);
  }

  function createBanner(className, message) {
    const banner = document.createElement('div');
    banner.className = className;
    banner.textContent = message;
    document.body.appendChild(banner);
    dismissAfterDelay(banner);
  }

  function showNotification(message) {
    createBanner('notification', message);
  }

  function showErrorNotification(message) {
    createBanner('error-notification', message);
  }

  function normalizePrefix(prefix) {
    if (!prefix || prefix === '/') {
      return '';
    }
    return prefix.endsWith('/') ? prefix.slice(0, -1) : prefix;
  }

  function buildBaseUrl(protocol, prefix) {
    const normalizedProtocol = protocol
      ? protocol.replace(/:+$/, '')
      : window.location.protocol.replace(':', '');
    const normalizedPrefix = normalizePrefix(prefix);
    return `${normalizedProtocol}://${window.location.host}${normalizedPrefix}`;
  }

  function setupAutoRefresh(toggleSelector, refreshFn, intervalMs = 5000) {
    let enabled = true;
    let timerId = null;
    const toggle = document.querySelector(toggleSelector);

    const start = () => {
      if (timerId) {
        clearInterval(timerId);
      }
      timerId = window.setInterval(refreshFn, intervalMs);
    };

    const stop = () => {
      if (timerId) {
        clearInterval(timerId);
        timerId = null;
      }
    };

    const refresh = () => {
      if (enabled) {
        refreshFn();
      }
    };

    if (toggle) {
      enabled = toggle.checked;
      if (enabled) {
        start();
      }
      toggle.addEventListener('change', () => {
        enabled = toggle.checked;
        if (enabled) {
          start();
          showNotification('Autorefresh enabled');
        } else {
          stop();
          showNotification('Autorefresh disabled');
        }
      });
    } else {
      start();
    }

    return {
      refresh,
      isEnabled: () => enabled,
      stop,
    };
  }

  function highlightActiveNav() {
    const navLinks = document.querySelectorAll('.header-link');
    if (!navLinks.length) {
      return;
    }

    const currentPath = window.location.pathname.replace(/\/+$/, '') || '/';

    navLinks.forEach((link) => {
      const linkPath =
        new URL(link.getAttribute('href'), window.location.origin).pathname.replace(/\/+$/, '') ||
        '/';
      if (linkPath === currentPath) {
        link.classList.add('selected');
      }
    });
  }

  window.dashboardHelpers = {
    buildBaseUrl,
    showNotification,
    showErrorNotification,
    setupAutoRefresh,
  };

  document.addEventListener('DOMContentLoaded', highlightActiveNav);
})(window, document);

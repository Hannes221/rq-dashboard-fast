;(function () {
  const body = document.body;
  const dataset = (body && body.dataset) || {};
  const rawProtocol = dataset.protocol || window.location.protocol;
  const normalizedProtocol = rawProtocol.replace(/:$/, '');
  const prefix = dataset.prefix || '';
  const baseUrl = `${normalizedProtocol}://${window.location.host}${prefix}`;

  const removeTrailingSlash = (value) =>
    value.length > 1 && value.endsWith('/') ? value.slice(0, -1) : value;

  const spawnNotification = (message, variant) => {
    if (!body) {
      return;
    }
    const element = document.createElement('div');
    element.className = variant === 'error' ? 'error-notification' : 'notification';
    element.textContent = message;
    body.appendChild(element);
    setTimeout(() => {
      element.remove();
    }, 3200);
  };

  const highlightActiveNav = () => {
    const currentPath = removeTrailingSlash(window.location.pathname);
    document.querySelectorAll('.header-link').forEach((link) => {
      const linkPath = removeTrailingSlash(new URL(link.href, window.location.origin).pathname);
      if (linkPath === currentPath) {
        link.classList.add('header-link--active');
      }
    });
  };

  const createAutoRefresh = (callback, interval = 5000, startEnabled = true) => {
    let enabled = Boolean(startEnabled);
    let timerId = null;

    const stop = () => {
      if (timerId) {
        clearInterval(timerId);
        timerId = null;
      }
    };

    const start = () => {
      if (!enabled || timerId) {
        return;
      }
      timerId = setInterval(() => {
        if (enabled) {
          callback();
        }
      }, interval);
    };

    const setEnabled = (value) => {
      enabled = Boolean(value);
      if (enabled) {
        callback();
        start();
      } else {
        stop();
      }
    };

    if (enabled) {
      callback();
      start();
    }

    return {
      setEnabled,
      start,
      stop,
      isEnabled: () => enabled,
    };
  };

  window.dashboard = {
    baseUrl,
    notify: (message) => spawnNotification(message, 'info'),
    notifyError: (message) => spawnNotification(message, 'error'),
    createAutoRefresh,
  };

  document.addEventListener('DOMContentLoaded', highlightActiveNav);
})();

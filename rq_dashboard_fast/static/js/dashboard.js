(() => {
  const NOTIFICATION_DURATION = 3000;

  const getPrefix = () => {
    const body = document.body;
    return body ? body.dataset.prefix || '' : '';
  };

  const prefix = getPrefix();
  const baseUrl = `${window.location.protocol}//${window.location.host}${prefix}`;

  const buildNotification = (message, variant) => {
    const notification = document.createElement('div');
    notification.className = `notification notification--${variant}`;
    notification.textContent = message;

    document.body.appendChild(notification);

    window.setTimeout(() => {
      notification.remove();
    }, NOTIFICATION_DURATION);
  };

  const showMessage = (message) => buildNotification(message, 'info');
  const showError = (message) => buildNotification(message, 'error');

  const normalizePath = (value) => value.replace(/\/+$/, '') || '/';

  const highlightActiveNavLink = () => {
    const currentPath = normalizePath(window.location.pathname);
    const rootPath = normalizePath(prefix || '/');
    const navLinks = document.querySelectorAll('[data-nav-link]');

    navLinks.forEach((link) => {
      const targetPath = normalizePath(new URL(link.href, window.location.origin).pathname);
      const target = link.dataset.navLink;
      const isRootJobsLink = target === 'jobs' && currentPath === rootPath;

      if (currentPath === targetPath || isRootJobsLink) {
        link.classList.add('is-active');
        link.setAttribute('aria-current', 'page');
      } else {
        link.classList.remove('is-active');
        link.removeAttribute('aria-current');
      }
    });
  };

  const initAutoRefresh = (toggleSelector, refreshFn, intervalMs = 5000) => {
    const toggle = document.querySelector(toggleSelector);
    if (!toggle || typeof refreshFn !== 'function') {
      return { start: () => {}, stop: () => {} };
    }

    let intervalId = null;

    const start = () => {
      if (intervalId) {
        return;
      }
      intervalId = window.setInterval(refreshFn, intervalMs);
      toggle.checked = true;
    };

    const stop = () => {
      if (!intervalId) {
        return;
      }
      window.clearInterval(intervalId);
      intervalId = null;
      toggle.checked = false;
    };

    const handleToggleChange = () => {
      if (toggle.checked) {
        refreshFn();
        start();
      } else {
        stop();
      }
    };

    toggle.addEventListener('change', handleToggleChange);

    if (toggle.checked) {
      refreshFn();
      start();
    }

    return { start, stop, refresh: refreshFn };
  };

  const fetchJson = (path, options = {}) => {
    const url = path.startsWith('http') ? path : `${baseUrl}${path}`;
    return fetch(url, options).then((response) => {
      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`);
      }
      return response.json();
    });
  };

  window.dashboard = {
    prefix,
    baseUrl,
    showMessage,
    showError,
    initAutoRefresh,
    fetchJson,
  };

  document.addEventListener('DOMContentLoaded', highlightActiveNavLink);
})();

(() => {
  'use strict';

  const config = window.dashboardConfig || {};
  const DEFAULT_INTERVAL = 5000;

  const getPrefix = () => config.prefix || '';

  const getBaseUrl = () => {
    const protocol =
      config.protocol ||
      (window.location.protocol ? window.location.protocol.replace(':', '') : 'http');
    const host = window.location.host;
    return `${protocol}://${host}${getPrefix()}`;
  };

  const showNotification = (message, variant = 'info') => {
    if (!message) {
      return;
    }

    const existing = document.querySelector('.notification, .error-notification');
    if (existing) {
      existing.remove();
    }

    const node = document.createElement('div');
    node.className = variant === 'error' ? 'error-notification' : 'notification';
    node.textContent = message;
    document.body.appendChild(node);

    setTimeout(() => {
      node.remove();
    }, 3200);
  };

  const showError = (message) => showNotification(message, 'error');

  const setupAutoRefresh = ({ checkboxSelector, interval = DEFAULT_INTERVAL, onRefresh }) => {
    if (typeof onRefresh !== 'function') {
      throw new Error('onRefresh callback is required');
    }

    const checkbox = checkboxSelector ? document.querySelector(checkboxSelector) : null;
    let enabled = checkbox ? checkbox.checked : true;
    let timerId = null;

    const stop = () => {
      if (timerId) {
        window.clearInterval(timerId);
        timerId = null;
      }
    };

    const start = () => {
      if (!enabled || timerId) {
        return;
      }
      timerId = window.setInterval(onRefresh, interval);
    };

    const sync = () => {
      if (enabled) {
        start();
      } else {
        stop();
      }
    };

    if (checkbox) {
      checkbox.addEventListener('change', () => {
        enabled = checkbox.checked;
        showNotification(`Autorefresh ${enabled ? 'enabled' : 'disabled'}`);
        sync();
      });
    }

    if (enabled) {
      start();
    }

    return {
      isEnabled: () => enabled,
      start: () => {
        enabled = true;
        if (checkbox) {
          checkbox.checked = true;
        }
        sync();
      },
      stop: () => {
        enabled = false;
        if (checkbox) {
          checkbox.checked = false;
        }
        sync();
      },
      trigger: () => onRefresh(),
    };
  };

  const requestJson = async (url, options = {}) => {
    const response = await fetch(url, options);
    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status}`);
    }
    return response.json();
  };

  const downloadBlob = (blob, filename) => {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  };

  const markActiveNav = () => {
    const navRoot = document.querySelector('[data-nav-root]');
    if (!navRoot) {
      return;
    }

    const prefix = getPrefix();
    const currentPath = window.location.pathname;
    const normalized =
      prefix && currentPath.startsWith(prefix) ? currentPath.slice(prefix.length) : currentPath;

    navRoot.querySelectorAll('[data-nav-path]').forEach((link) => {
      const route = link.getAttribute('data-nav-path') || '/';
      const isActive =
        route === '/'
          ? normalized === '/' || normalized === ''
          : normalized.startsWith(route);
      link.classList.toggle('is-active', isActive);
    });
  };

  document.addEventListener('DOMContentLoaded', markActiveNav);

  window.DashboardUI = {
    getPrefix,
    getBaseUrl,
    requestJson,
    showNotification,
    showError,
    setupAutoRefresh,
    downloadBlob,
  };
})();

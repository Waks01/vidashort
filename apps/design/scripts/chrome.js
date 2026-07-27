/* ========================================================================
   vidashort — Shared chrome (topbar + bottomnav)
   Renders into <div id="chrome-topbar"> and <div id="chrome-bottomnav">
   Uses the role set in vidashort.Storage to pick the right tab set.
   ======================================================================== */
(function () {
  'use strict';
  const E = (window.vidashort && window.vidashort.MockData && window.vidashort.MockData.ECONOMY) || {};

  // Tab sets per role
  const TABS = {
    viewer: [
      { id: 'home',     label: 'Home',     icon: 'house',          href: './10-home.html' },
      { id: 'discover', label: 'Discover', icon: 'compass',        href: './11-discover.html' },
      { id: 'library',  label: 'Library',  icon: 'bookmark-simple',href: './20-library.html' },
      { id: 'wallet',   label: 'Wallet',   icon: 'wallet',         href: './21-wallet.html' },
      { id: 'profile',  label: 'Profile',  icon: 'user-circle',    href: './30-profile.html' },
    ],
    creator: [
      { id: 'dash',    label: 'Dashboard', icon: 'gauge',         href: './50-creator-dashboard.html' },
      { id: 'series',  label: 'My series', icon: 'film-strip',    href: './51-creator-series.html' },
      { id: 'upload',  label: 'Upload',    icon: 'upload-simple', href: './52-creator-upload.html' },
      { id: 'payouts', label: 'Payouts',   icon: 'money',         href: './54-creator-payouts.html' },
      { id: 'profile', label: 'Account',   icon: 'user-circle',   href: './30-profile.html' },
    ],
    admin: [
      { id: 'over',     label: 'Overview', icon: 'gauge',          href: './60-admin-overview.html' },
      { id: 'mod',      label: 'Moderate', icon: 'shield-check',   href: './61-admin-moderation.html' },
      { id: 'content',  label: 'Content',  icon: 'film-strip',     href: './62-admin-content.html' },
      { id: 'users',    label: 'Users',    icon: 'users',          href: './63-admin-users.html' },
      { id: 'ads',      label: 'Ads',      icon: 'megaphone',      href: './64-admin-ads.html' },
    ],
  };

  function activeKey() {
    const file = (location.pathname.split('/').pop() || '').toLowerCase();
    if (/^10-home|^11-discover|^20-library|^21-wallet|^30-profile/.test(file)) {
      if (/^10-home/.test(file)) return 'home';
      if (/^11-discover/.test(file)) return 'discover';
      if (/^20-library/.test(file)) return 'library';
      if (/^21-wallet/.test(file)) return 'wallet';
      if (/^30-profile/.test(file)) return 'profile';
    }
    if (/^50-creator-dashboard/.test(file)) return 'dash';
    if (/^51-creator-series/.test(file))    return 'series';
    if (/^52-creator-upload/.test(file))    return 'upload';
    if (/^54-creator-payouts/.test(file))   return 'payouts';
    if (/^60-admin-overview/.test(file))    return 'over';
    if (/^61-admin-moderation/.test(file))  return 'mod';
    if (/^62-admin-content/.test(file))     return 'content';
    if (/^63-admin-users/.test(file))       return 'users';
    if (/^64-admin-ads/.test(file))         return 'ads';
    return null;
  }

  function renderTopbar() {
    const host = document.getElementById('chrome-topbar');
    if (!host) return;
    const role = vidashort.Storage.getRole();
    const auth = vidashort.Storage.getAuth();
    const coins = vidashort.Storage.getCoins();
    const isVip = vidashort.Storage.isVIP();
    const title = host.dataset.title || '';
    const showBack = host.dataset.back === 'true';

    host.outerHTML = `
      <header class="topbar">
        <div class="topbar__left">
          ${showBack ? '<button class="topbar__back" data-tap data-nav="back"><i class="ph ph-arrow-left"></i></button>' : ''}
          <span class="topbar__title">${title || (role === 'creator' ? 'Creator Studio' : role === 'admin' ? 'Admin' : 'vidashort')}</span>
        </div>
        <div class="topbar__right">
          ${role === 'admin' ? '' : `<button class="topbar__action" data-tap data-nav="wallet" title="Wallet"><i class="ph ph-bell"></i></button>
          <button class="coin-badge" data-tap data-nav="wallet" title="Wallet">
            <i class="ph-fill ph-coins"></i>
            <span>${coins.toLocaleString()}</span>
          </button>`}
          ${auth ? `<button class="topbar__action" data-tap data-nav="profile" title="Account"><i class="ph ph-user-circle"></i></button>` : ''}
        </div>
      </header>
    `;
  }

  function renderBottomnav() {
    const host = document.getElementById('chrome-bottomnav');
    if (!host) return;
    const role = vidashort.Storage.getRole();
    const tabs = TABS[role] || TABS.viewer;
    const active = activeKey();
    host.outerHTML = `
      <nav class="bottomnav">
        ${tabs.map(t => `
          <a class="bottomnav__item ${t.id === active ? 'bottomnav__item--active' : ''}" href="${t.href}" data-tap data-nav="tab" data-tab="${t.id}">
            <i class="ph ${t.id === active ? 'ph-fill' : 'ph'} ${t.icon}"></i>
            <span>${t.label}</span>
          </a>
        `).join('')}
      </nav>
    `;
  }

  function wireNav() {
    document.addEventListener('click', (e) => {
      const nav = e.target.closest('[data-nav]');
      if (!nav) return;
      const which = nav.dataset.nav;
      if (which === 'back') { vidashort.Router.back(); return; }
      if (which === 'tab') return; // let <a> navigate
      const map = {
        wallet:  './21-wallet.html',
        profile: './30-profile.html',
      };
      if (map[which]) { e.preventDefault(); vidashort.Router.go(map[which]); }
    });
  }

  // Auto-mount on every screen that includes the script
  function mount() {
    renderTopbar();
    renderBottomnav();
    wireNav();
    renderIndexFab();
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mount);
  } else {
    mount();
  }

  // Floating "back to index" button — always visible on every screen
  function renderIndexFab() {
    if (document.getElementById('index-fab')) return;
    const fab = document.createElement('a');
    fab.id = 'index-fab';
    fab.href = '../index.html';
    fab.title = 'Back to prototype index';
    fab.dataset.tap = '';
    fab.innerHTML = '<i class="ph-bold ph-list"></i><span>Index</span>';
    document.body.appendChild(fab);
  }
})();

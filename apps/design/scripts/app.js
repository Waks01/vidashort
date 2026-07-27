/* ========================================================================
   vidashort — Core app helpers
   Router, Modal, Toast, Confetti, Storage, AdCap, CreatorLedger, Auth

   Exposed as window.vidashort.{...}
   ======================================================================== */

(function () {
  'use strict';

  const PREFIX = 'vidashort.';
  const E = (window.vidashort && window.vidashort.MockData && window.vidashort.MockData.ECONOMY) || {
    coinsPerNaira: 10,
    episodeCostCoins: 25,
    adRewardCoins: 20,
    dailyAdCap: 100,
    revenueSplit: { platform: 0.40, creator: 0.60 },
    payoutThresholdCoins: 50000,
    coinsToNaira(c) { return +(c / 10).toFixed(2); },
    nairaToCoins(n) { return Math.floor(n * 10); },
  };

  // ============== Storage ==============
  const Storage = {
    get(key, fallback = null) {
      try {
        const raw = localStorage.getItem(PREFIX + key);
        return raw == null ? fallback : JSON.parse(raw);
      } catch (e) { return fallback; }
    },
    set(key, value) {
      try { localStorage.setItem(PREFIX + key, JSON.stringify(value)); }
      catch (e) { console.warn('Storage.set failed', e); }
    },
    remove(key) { localStorage.removeItem(PREFIX + key); },
    clear() {
      Object.keys(localStorage)
        .filter((k) => k.startsWith(PREFIX))
        .forEach((k) => localStorage.removeItem(k));
    },
    // ---------- Wallet ----------
    getCoins() { return this.get('user.coins', 120); },
    setCoins(n) { this.set('user.coins', Math.max(0, Math.floor(n))); },
    addCoins(n, reason = 'manual', meta = {}) {
      const before = this.getCoins();
      const after = before + n;
      this.setCoins(after);
      this.appendLedger({ delta: n, reason, balanceAfter: after, ...meta });
      return after;
    },
    spendCoins(n, reason = 'spend', meta = {}) {
      if (this.getCoins() < n) return false;
      this.addCoins(-n, reason, meta);
      return true;
    },
    appendLedger(entry) {
      const ledger = this.get('user.ledger', []);
      ledger.unshift({ ...entry, at: new Date().toISOString() });
      this.set('user.ledger', ledger.slice(0, 200));
    },
    // ---------- VIP ----------
    isVIP() {
      const until = this.get('user.vipUntil', 0);
      return Date.now() < until;
    },
    setVIP(days) { this.set('user.vipUntil', Date.now() + days * 86400000); },
    cancelVIP() { this.set('user.vipUntil', 0); },
    // ---------- Streak ----------
    getStreak() { return this.get('user.dailyStreak', { day: 0, lastClaimedOn: null }); },
    setStreak(s) { this.set('user.dailyStreak', s); },
    // ---------- Favorites ----------
    getFavorites() { return this.get('user.favorites', []); },
    toggleFavorite(id) {
      const f = this.getFavorites();
      const i = f.indexOf(id);
      if (i >= 0) f.splice(i, 1); else f.push(id);
      this.set('user.favorites', f);
      return i < 0;
    },
    // ---------- Watch history ----------
    getWatchHistory() { return this.get('user.watchHistory', []); },
    recordWatch(episodeId, positionS, completed) {
      const h = this.getWatchHistory().filter((w) => w.episodeId !== episodeId);
      h.unshift({ episodeId, positionS, completed, at: Date.now() });
      this.set('user.watchHistory', h.slice(0, 50));
    },
    episodesWatched() { return this.get('episodesWatched', 0); },
    incEpisodesWatched() { this.set('episodesWatched', this.episodesWatched() + 1); },
    // ---------- Onboarding ----------
    isOnboarded() { return !!this.get('user.onboarded', false); },
    setOnboarded() { this.set('user.onboarded', true); },
    getGenres() { return this.get('user.genres', []); },
    setGenres(g) { this.set('user.genres', g); },
    getAgeConfirmed() { return !!this.get('user.ageConfirmed', false); },
    setAgeConfirmed() { this.set('user.ageConfirmed', true); },
    // ---------- Auth ----------
    getAuth() { return this.get('user.auth', null); },
    setAuth(a) { this.set('user.auth', a); },
    signOut() { this.remove('user.auth'); },
    // ---------- Role ----------
    getRole() { return this.get('user.role', 'viewer'); },
    setRole(r) { this.set('user.role', r); },
    // ---------- Creator profile ----------
    getCreatorProfile() { return this.get('creator.profile', null); },
    setCreatorProfile(p) { this.set('creator.profile', p); },
    getCreatorSeries() { return this.get('creator.series', []); },
    setCreatorSeries(s) { this.set('creator.series', s); },
    getCreatorEarnings() {
      return this.get('creator.earnings', { lifetimeCoins: 0, pendingCoins: 0, lifetimeNaira: 0, pendingNaira: 0 });
    },
    addCreatorEarnings(coins, reason = 'unlock') {
      const e = this.getCreatorEarnings();
      e.lifetimeCoins += coins;
      e.pendingCoins += coins;
      e.lifetimeNaira = E.coinsToNaira(e.lifetimeCoins);
      e.pendingNaira = E.coinsToNaira(e.pendingCoins);
      this.set('creator.earnings', e);
      this.appendLedger({ delta: coins, reason, kind: 'creator_earning', balanceAfter: this.getCoins() });
      return e;
    },
  };

  // ============== AdCap (100 ads/day/user) ==============
  const todayStr = () => new Date().toISOString().slice(0, 10);
  const AdCap = {
    watchedToday() {
      const on = Storage.get('user.adsWatchedOn', todayStr());
      if (on !== todayStr()) {
        Storage.set('user.adsWatchedOn', todayStr());
        Storage.set('user.adsWatchedToday', 0);
        return 0;
      }
      return Storage.get('user.adsWatchedToday', 0);
    },
    remaining() { return Math.max(0, E.dailyAdCap - this.watchedToday()); },
    atCap() { return this.watchedToday() >= E.dailyAdCap; },
    canWatch() { return !Storage.isVIP() && this.remaining() > 0; },
    record() {
      Storage.set('user.adsWatchedToday', this.watchedToday() + 1);
      Storage.set('user.adsWatchedOn', todayStr());
    },
  };

  // ============== Paywall decision (coin → ad → premium) ==============
  // Returns the chosen path. UI uses this to render the right CTA order.
  const Paywall = {
    decide(episodeCost = E.episodeCostCoins) {
      if (Storage.isVIP()) return { path: 'vip',     label: 'Watch (VIP)', reason: 'Unlimited with VIP' };
      if (Storage.getCoins() >= episodeCost) return { path: 'coins',  label: `Use ${episodeCost} coins`, reason: `You have ${Storage.getCoins()} coins` };
      if (AdCap.canWatch())                  return { path: 'ad',     label: `Watch ad (+${E.adRewardCoins} coins)`, reason: `${AdCap.remaining()} ads left today` };
      return { path: 'premium', label: 'Go Premium', reason: 'You’ve used all your free options today' };
    },
    // attempt to pay for the episode; returns true if successful.
    // Priority: coins → ad → premium (which returns false, modal must show)
    payEpisode(episode, onAdStart) {
      if (Storage.isVIP()) return { ok: true, source: 'vip' };
      if (Storage.spendCoins(episode.requiredCoins, 'unlock', { episodeId: episode.id, seriesId: episode.seriesId })) {
        // credit creator earnings (60% of gross)
        if (episode.creatorId) {
          const creatorCoins = Math.floor(episode.requiredCoins * E.revenueSplit.creator);
          Storage.addCreatorEarnings(creatorCoins, 'unlock');
        }
        return { ok: true, source: 'coins' };
      }
      if (AdCap.canWatch()) {
        if (typeof onAdStart === 'function') onAdStart(episode);
        return { ok: true, source: 'ad-pending' };
      }
      return { ok: false, source: 'premium' };
    },
    claimRewarded() {
      if (Storage.isVIP()) return { ok: false, reason: 'vip' };
      if (AdCap.atCap())   return { ok: false, reason: 'cap' };
      AdCap.record();
      Storage.addCoins(E.adRewardCoins, 'rewarded_ad');
      return { ok: true, coins: E.adRewardCoins, remaining: AdCap.remaining() };
    },
  };

  // ============== Toast ==============
  const Toast = {
    show(message, variant = 'info', durationMs = 2500) {
      const existing = document.querySelector('.toast');
      if (existing) existing.remove();
      const el = document.createElement('div');
      el.className = `toast toast--${variant}`;
      const icon = { success: 'check-circle', error: 'x-circle', info: 'info' }[variant] || 'info';
      el.innerHTML = `<i class="ph ph-${icon}"></i><span>${message}</span>`;
      document.body.appendChild(el);
      setTimeout(() => {
        el.style.animation = 'fade-out 200ms forwards';
        setTimeout(() => el.remove(), 200);
      }, durationMs);
    },
  };

  // ============== Confetti ==============
  const Confetti = {
    burst({ count = 60, originX = 50, originY = 50 } = {}) {
      const colors = ['#ff1f5a', '#ffe27a', '#ffffff', '#ff4d80', '#d4a017'];
      for (let i = 0; i < count; i++) {
        const el = document.createElement('span');
        el.className = 'confetti';
        const angle = (i / count) * Math.PI * 2;
        const distance = 30 + Math.random() * 70;
        el.style.setProperty('--x', (originX + Math.cos(angle) * distance) + 'vw');
        el.style.setProperty('--rot', (Math.random() * 720 - 360) + 'deg');
        el.style.setProperty('--delay', (Math.random() * 200) + 'ms');
        el.style.setProperty('--color', colors[Math.floor(Math.random() * colors.length)]);
        el.style.top = (originY - 20) + 'vh';
        document.body.appendChild(el);
        setTimeout(() => el.remove(), 2400);
      }
    },
  };

  // ============== Modal ==============
  const Modal = {
    open(html, { dismissable = true, center = false, onClose } = {}) {
      const backdrop = document.createElement('div');
      backdrop.className = 'modal-backdrop' + (center ? ' modal-backdrop--center' : '');
      backdrop.innerHTML = `<div class="modal">${html}</div>`;
      const close = () => { Modal.close(); if (onClose) onClose(); };
      if (dismissable) {
        backdrop.addEventListener('click', (e) => { if (e.target === backdrop) close(); });
      }
      document.body.appendChild(backdrop);
      const focusable = backdrop.querySelectorAll('button, [href], input, [tabindex]:not([tabindex="-1"])');
      if (focusable.length) focusable[0].focus();
      return { backdrop, close };
    },
    close() {
      const backdrop = document.querySelector('.modal-backdrop');
      if (backdrop) backdrop.remove();
    },
  };

  // ============== Confirm ==============
  const Confirm = {
    open({ title, body, confirmLabel = 'Confirm', cancelLabel = 'Cancel', danger = false, onConfirm } = {}) {
      const { close } = Modal.open(`
        <div class="modal__header">
          <div class="modal__title">${title}</div>
        </div>
        <div class="modal__body">${body || ''}</div>
        <div class="modal__footer" style="display:flex; gap:12px;">
          <button class="btn btn--secondary btn--block" data-action="cancel">${cancelLabel}</button>
          <button class="btn btn--block ${danger ? 'btn--primary' : 'btn--gold'}" data-action="confirm" style="${danger ? 'background:var(--gradient-accent);' : ''}">${confirmLabel}</button>
        </div>
      `, { dismissable: true, onClose: () => {} });
      document.querySelector('.modal [data-action="cancel"]').addEventListener('click', close);
      document.querySelector('.modal [data-action="confirm"]').addEventListener('click', () => {
        close();
        if (onConfirm) onConfirm();
      });
    },
  };

  // ============== Router ==============
  const Router = {
    go(url, opts = {}) {
      const main = document.querySelector('.screen');
      if (main && opts.direction) main.setAttribute('data-direction', opts.direction);
      setTimeout(() => { window.location.href = url; }, 60);
    },
    back() { history.back(); },
  };

  // ============== Coin counter animation ==============
  const animateCoinCount = (el, from, to, durationMs = 600) => {
    const start = performance.now();
    const tick = (now) => {
      const t = Math.min(1, (now - start) / durationMs);
      const eased = 1 - Math.pow(1 - t, 3);
      const val = Math.round(from + (to - from) * eased);
      el.textContent = val.toLocaleString();
      if (t < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  };

  // ============== Haptics ==============
  const Haptics = {
    tap() { if (navigator.vibrate) navigator.vibrate(10); },
    success() { if (navigator.vibrate) navigator.vibrate([10, 50, 10]); },
    error() { if (navigator.vibrate) navigator.vibrate([20, 30, 20]); },
  };

  // ============== Auth guard ==============
  const Auth = {
    requireUser() {
      if (!Storage.getAuth()) {
        Toast.show('Sign in to continue', 'info');
        Router.go('./04-auth-entry.html');
        return false;
      }
      return true;
    },
    requireRole(role) {
      if (!this.requireUser()) return false;
      if (Storage.getRole() !== role) {
        Toast.show(`Switch to ${role} to access this page`, 'info');
        Router.go(Storage.getRole() === 'creator' ? './50-creator-dashboard.html' : './10-home.html');
        return false;
      }
      return true;
    },
    isAdmin() { return Storage.getRole() === 'admin' || Storage.getRole() === 'creator' && Storage.get('user.isAdmin', false); },
  };

  // ============== Utility: tap handler that vibrates ==============
  document.addEventListener('click', (e) => {
    const target = e.target.closest('button, a, .clickable, [data-tap]');
    if (!target) return;
    if (target.disabled || target.getAttribute('aria-disabled') === 'true') return;
    Haptics.tap();
  }, true);

  // ============== Public API ==============
  // Merge into existing vidashort (preserves MockData attached by data.js)
  window.vidashort = Object.assign(window.vidashort || {}, {
    Storage,
    AdCap,
    Paywall,
    Toast,
    Confetti,
    Modal,
    Confirm,
    Router,
    Haptics,
    Auth,
    animateCoinCount,
  });
})();

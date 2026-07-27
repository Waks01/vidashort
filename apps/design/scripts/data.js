/* ========================================================================
   vidashort — Mock data
   All sample content. Hand-written to feel like real microdramas.
   Exposed as window.vidashort.MockData

   Economics (locked-in):
     - 10 coins  =  ₦1
     - Episode unlock = 25 coins (₦2.50)
     - Rewarded ad   = 20 coins (₦2.00)
     - Daily ad cap  = 100 ads / user / day
     - Revenue split = 60% creator-loyalty / 40% platform
   ======================================================================== */

(function () {
  'use strict';

  // ============== Image helpers ==============
  // picsum.photos seeded URL — stable per slug (used as TMDB fallback).
  const picsum = (slug, w = 540, h = 960) => `https://picsum.photos/seed/${slug}/${w}/${h}`;
  const avatar = (slug) => `https://i.pravatar.cc/150?u=${slug}`;

  // ============== TMDB adapter (mock + real) ==============
  // TMDB base image URL: https://image.tmdb.org/t/p/{size}/{path}
  // For the prototype, we synthesize a TMDB-shaped object from a slug.
  // Replace poster() / still() with real TMDB API calls when keys are wired.
  const TMDB_IMG = 'https://image.tmdb.org/t/p';
  const TMDB = {
    poster(slug, size = 'w500')  { return `${TMDB_IMG}/${size}/${slug}.jpg`; },
    still(slug, size = 'w300')   { return `${TMDB_IMG}/${size}/${slug}.jpg`; },
    // Fallback to picsum if a TMDB key isn't wired yet.
    safe(slug, w = 540, h = 960) { return picsum(slug, w, h); },
  };

  // ============== Economics ==============
  const ECONOMY = {
    coinsPerNaira: 10,            // 10 coins = ₦1
    episodeCostCoins: 25,         // 25 coins = ₦2.50 per episode unlock
    adRewardCoins: 20,            // 20 coins = ₦2.00 per rewarded ad
    dailyAdCap: 100,              // max rewarded ads per user per day
    revenueSplit: {               // earned revenue from episode unlocks
      platform: 0.40,             // 40% to vidashort
      creator:  0.60,             // 60% to creator (as loyalty points)
    },
    payoutThresholdCoins: 50000,  // 50000 coins = ₦5,000 — minimum cashout
    // Conversion helpers
    coinsToNaira(c)  { return +(c / this.coinsPerNaira).toFixed(2); },
    nairaToCoins(n)  { return Math.floor(n * this.coinsPerNaira); },
  };

  // ============== Series (3 originals, TMDB-linked) ==============
  const series = [
    {
      id: 's1',
      slug: 'ceos-secret-heir',
      title: "The CEO's Secret Heir",
      synopsis: "When a ruthless billionaire discovers the daughter he never knew existed, he'll do anything to keep her — even marry the mother he abandoned.",
      cover: TMDB.poster('ceosecretheir'),
      backdrop: TMDB.poster('ceosecretheir', 'w1280'),
      language: 'en',
      region: 'WW',
      totalEpisodes: 10,
      isOriginal: true,
      isCreator: false,
      creatorId: null,
      copyrightOwner: 'vidashort originals',
      allowedCountries: ['US', 'CA', 'GB', 'AU', 'NZ', 'IE', 'NG', 'GH', 'KE', 'ZA'],
      tags: ['Romance', 'CEO', 'Billionaire', 'Secret Baby'],
      category: 'Romance',
      tmdbId: 199950,
      hot: true,
      views: 1842303,
      rating: 4.7,
      episodes: [
        { number: 1,  title: 'The Wedding That Wasn\'t',                durationS: 75, still: TMDB.still('ceosecretheir_e1'),  requiredCoins: 0,  isFree: true,  isPaywalled: false, adPreroll: false, adMidroll: false },
        { number: 2,  title: 'A Contract She Shouldn\'t Have Signed',  durationS: 80, still: TMDB.still('ceosecretheir_e2'),  requiredCoins: 0,  isFree: true,  isPaywalled: false, adPreroll: false, adMidroll: false },
        { number: 3,  title: 'The Heir He Never Knew',                  durationS: 78, still: TMDB.still('ceosecretheir_e3'),  requiredCoins: 0,  isFree: true,  isPaywalled: false, adPreroll: false, adMidroll: false },
        { number: 4,  title: 'Five Years of Silence',                   durationS: 82, still: TMDB.still('ceosecretheir_e4'),  requiredCoins: 0,  isFree: true,  isPaywalled: false, adPreroll: false, adMidroll: false },
        { number: 5,  title: 'The First Time He Saw Her',               durationS: 76, still: TMDB.still('ceosecretheir_e5'),  requiredCoins: 0,  isFree: true,  isPaywalled: false, adPreroll: false, adMidroll: false },
        { number: 6,  title: 'A DNA Test Changes Everything',           durationS: 85, still: TMDB.still('ceosecretheir_e6'),  requiredCoins: ECONOMY.episodeCostCoins, isFree: false, isPaywalled: true,  adPreroll: true,  adMidroll: true },
        { number: 7,  title: 'He Won\'t Let Her Walk Away',            durationS: 80, still: TMDB.still('ceosecretheir_e7'),  requiredCoins: ECONOMY.episodeCostCoins, isFree: false, isPaywalled: true,  adPreroll: true,  adMidroll: false },
        { number: 8,  title: 'The Past Comes Knocking',                 durationS: 88, still: TMDB.still('ceosecretheir_e8'),  requiredCoins: ECONOMY.episodeCostCoins, isFree: false, isPaywalled: true,  adPreroll: true,  adMidroll: true },
        { number: 9,  title: 'She Disappears at Midnight',              durationS: 82, still: TMDB.still('ceosecretheir_e9'),  requiredCoins: ECONOMY.episodeCostCoins, isFree: false, isPaywalled: true,  adPreroll: true,  adMidroll: false },
        { number: 10, title: 'The Choice That Breaks Her',              durationS: 90, still: TMDB.still('ceosecretheir_e10'), requiredCoins: ECONOMY.episodeCostCoins, isFree: false, isPaywalled: true,  adPreroll: true,  adMidroll: true },
      ],
    },
    {
      id: 's2',
      slug: 'rejected-by-the-alpha',
      title: 'Rejected by the Alpha',
      synopsis: "She was the pack's weakest wolf — until the day the future Alpha rejected her. Now, three years later, she's back, and she's not what she seems.",
      cover: TMDB.poster('rejectedalpha'),
      backdrop: TMDB.poster('rejectedalpha', 'w1280'),
      language: 'en',
      region: 'WW',
      totalEpisodes: 10,
      isOriginal: true,
      isCreator: false,
      creatorId: null,
      copyrightOwner: 'vidashort originals',
      allowedCountries: ['US', 'CA', 'GB', 'AU', 'NZ', 'IE', 'ZA', 'NG'],
      tags: ['Werewolf', 'Romance', 'Revenge', 'Fantasy'],
      category: 'Werewolf',
      tmdbId: 63174,
      hot: true,
      views: 942108,
      rating: 4.6,
      episodes: [
        { number: 1,  title: 'The Rejection Ceremony',                  durationS: 78, still: TMDB.still('rejectedalpha_e1'),  requiredCoins: 0,  isFree: true,  isPaywalled: false, adPreroll: false, adMidroll: false },
        { number: 2,  title: 'The Wolf Without a Pack',                durationS: 75, still: TMDB.still('rejectedalpha_e2'),  requiredCoins: 0,  isFree: true,  isPaywalled: false, adPreroll: false, adMidroll: false },
        { number: 3,  title: 'Three Years of Training',                durationS: 82, still: TMDB.still('rejectedalpha_e3'),  requiredCoins: 0,  isFree: true,  isPaywalled: false, adPreroll: false, adMidroll: false },
        { number: 4,  title: 'The New Alpha',                          durationS: 80, still: TMDB.still('rejectedalpha_e4'),  requiredCoins: 0,  isFree: true,  isPaywalled: false, adPreroll: false, adMidroll: false },
        { number: 5,  title: 'She Returns',                            durationS: 76, still: TMDB.still('rejectedalpha_e5'),  requiredCoins: 0,  isFree: true,  isPaywalled: false, adPreroll: false, adMidroll: false },
        { number: 6,  title: 'He Doesn\'t Recognize Her',              durationS: 85, still: TMDB.still('rejectedalpha_e6'),  requiredCoins: ECONOMY.episodeCostCoins, isFree: false, isPaywalled: true,  adPreroll: true,  adMidroll: true },
        { number: 7,  title: 'The First Challenge',                    durationS: 80, still: TMDB.still('rejectedalpha_e7'),  requiredCoins: ECONOMY.episodeCostCoins, isFree: false, isPaywalled: true,  adPreroll: true,  adMidroll: false },
        { number: 8,  title: 'A Secret That Changes the Pack',         durationS: 88, still: TMDB.still('rejectedalpha_e8'),  requiredCoins: ECONOMY.episodeCostCoins, isFree: false, isPaywalled: true,  adPreroll: true,  adMidroll: true },
        { number: 9,  title: 'The Moon Rises',                         durationS: 82, still: TMDB.still('rejectedalpha_e9'),  requiredCoins: ECONOMY.episodeCostCoins, isFree: false, isPaywalled: true,  adPreroll: true,  adMidroll: false },
        { number: 10, title: 'Claimed by the Alpha',                   durationS: 90, still: TMDB.still('rejectedalpha_e10'), requiredCoins: ECONOMY.episodeCostCoins, isFree: false, isPaywalled: true,  adPreroll: true,  adMidroll: true },
      ],
    },
    {
      id: 's3',
      slug: 'rebirth-of-the-queen',
      title: 'Rebirth of the Queen',
      synopsis: "Betrayed by her husband and best friend, she died in a burning mansion. Now she's woken up ten years in the past, with every intention of destroying them both.",
      cover: TMDB.poster('rebirthqueen'),
      backdrop: TMDB.poster('rebirthqueen', 'w1280'),
      language: 'en',
      region: 'WW',
      totalEpisodes: 10,
      isOriginal: true,
      isCreator: false,
      creatorId: null,
      copyrightOwner: 'vidashort originals',
      allowedCountries: ['US', 'CA', 'GB', 'AU', 'NZ', 'IE', 'NG', 'KE'],
      tags: ['Rebirth', 'Revenge', 'Strong Female Lead', 'Drama'],
      category: 'Rebirth',
      tmdbId: 95440,
      hot: false,
      views: 612450,
      rating: 4.8,
      episodes: [
        { number: 1,  title: 'The Fire That Killed Her',               durationS: 78, still: TMDB.still('rebirthqueen_e1'),  requiredCoins: 0,  isFree: true,  isPaywalled: false, adPreroll: false, adMidroll: false },
        { number: 2,  title: 'Waking Up in the Past',                  durationS: 80, still: TMDB.still('rebirthqueen_e2'),  requiredCoins: 0,  isFree: true,  isPaywalled: false, adPreroll: false, adMidroll: false },
        { number: 3,  title: 'The Husband She Once Loved',             durationS: 75, still: TMDB.still('rebirthqueen_e3'),  requiredCoins: 0,  isFree: true,  isPaywalled: false, adPreroll: false, adMidroll: false },
        { number: 4,  title: 'The Best Friend\'s Betrayal',            durationS: 82, still: TMDB.still('rebirthqueen_e4'),  requiredCoins: 0,  isFree: true,  isPaywalled: false, adPreroll: false, adMidroll: false },
        { number: 5,  title: 'The First Counter-Move',                 durationS: 78, still: TMDB.still('rebirthqueen_e5'),  requiredCoins: 0,  isFree: true,  isPaywalled: false, adPreroll: false, adMidroll: false },
        { number: 6,  title: 'He Notices Something Different',          durationS: 85, still: TMDB.still('rebirthqueen_e6'),  requiredCoins: ECONOMY.episodeCostCoins, isFree: false, isPaywalled: true,  adPreroll: true,  adMidroll: true },
        { number: 7,  title: 'A Public Humiliation',                    durationS: 80, still: TMDB.still('rebirthqueen_e7'),  requiredCoins: ECONOMY.episodeCostCoins, isFree: false, isPaywalled: true,  adPreroll: true,  adMidroll: false },
        { number: 8,  title: 'The Boardroom War Begins',                durationS: 88, still: TMDB.still('rebirthqueen_e8'),  requiredCoins: ECONOMY.episodeCostCoins, isFree: false, isPaywalled: true,  adPreroll: true,  adMidroll: true },
        { number: 9,  title: 'Secrets in the Safe',                     durationS: 82, still: TMDB.still('rebirthqueen_e9'),  requiredCoins: ECONOMY.episodeCostCoins, isFree: false, isPaywalled: true,  adPreroll: true,  adMidroll: false },
        { number: 10, title: 'The Queen Returns',                       durationS: 90, still: TMDB.still('rebirthqueen_e10'), requiredCoins: ECONOMY.episodeCostCoins, isFree: false, isPaywalled: true,  adPreroll: true,  adMidroll: true },
      ],
    },
  ];

  // Flat list of all episodes across all series (for the home feed)
  const allEpisodes = series.flatMap((s) =>
    s.episodes.map((e) => ({
      ...e,
      seriesId: s.id,
      seriesTitle: s.title,
      seriesCover: s.cover,
      seriesSlug: s.slug,
      category: s.category,
    }))
  );

  // ============== Coin packs (Naira-denominated) ==============
  // 10 coins = ₦1. Aligns with Nigerian mobile-money tiers (OPay, PalmPay, Moniepoint).
  const coinPacks = [
    { id: 'coins_10',     coins: 10,    bonusCoins: 0,    priceNaira: 100,    badge: null },
    { id: 'coins_50',     coins: 50,    bonusCoins: 0,    priceNaira: 500,    badge: null },
    { id: 'coins_220',    coins: 200,   bonusCoins: 20,   priceNaira: 2000,   badge: 'BEST VALUE' },
    { id: 'coins_600',    coins: 500,   bonusCoins: 100,  priceNaira: 5000,   badge: null },
    { id: 'coins_1900',   coins: 1500,  bonusCoins: 400,  priceNaira: 15000,  badge: 'MOST POPULAR' },
  ];

  // ============== VIP plans (Naira) ==============
  const vipPlans = [
    { id: 'vip_weekly',  interval: 'weekly',  priceNaira: 500,   perMonth: 2000,  save: null,  trialDays: 3 },
    { id: 'vip_monthly', interval: 'monthly', priceNaira: 2000,  perMonth: 2000,  save: null,  trialDays: 3 },
    { id: 'vip_yearly',  interval: 'yearly',  priceNaira: 14000, perMonth: 1166,  save: 40,    trialDays: 7 },
  ];

  // ============== Genres (filter chips) ==============
  const genres = [
    'Romance', 'CEO', 'Billionaire', 'Werewolf', 'Rebirth',
    'Revenge', 'Fantasy', 'Thriller', 'Family', 'Historical', 'Mafia', 'Medical',
  ];

  // ============== Trending search tags ==============
  const trendingTags = [
    'CEO Romance', 'Rebirth', 'Werewolf', 'Revenge', 'Billionaire', 'Pregnant', 'Twins', 'Marriage',
  ];

  // ============== Comments ==============
  const sampleComments = [
    { id: 'c1', user: 'rosepetal_22',    avatar: avatar('rose'),     body: 'OMG the ending of episode 3 broke me 😭', likes: 2342, timeAgo: '2h',  pinned: true },
    { id: 'c2', user: 'bingedramma_99',  avatar: avatar('binge'),    body: 'who else is here at 2am because they CANNOT stop watching', likes: 1129, timeAgo: '4h' },
    { id: 'c3', user: 'coffeeglob',      avatar: avatar('coffee'),   body: 'this man is making me feel things i forgot i could feel', likes: 887,  timeAgo: '6h' },
    { id: 'c4', user: 'midnightwitch',   avatar: avatar('witch'),    body: 'i need season 2 immediately', likes: 654,  timeAgo: '8h' },
    { id: 'c5', user: 'popcornfiend',    avatar: avatar('popcorn'),  body: 'episode 6 when he saw her for the first time... i ascended', likes: 432, timeAgo: '12h' },
    { id: 'c6', user: 'tinderella',      avatar: avatar('tinderella'), body: 'uninstalled all dating apps after this', likes: 312, timeAgo: '1d' },
  ];

  // ============== Notifications ==============
  const sampleNotifications = [
    { id: 'n1', type: 'episode', seriesTitle: "The CEO's Secret Heir",  episodeNumber: 8,  body: 'New episode available!', timeAgo: '12m', unread: true },
    { id: 'n2', type: 'reward',  body: 'You earned 20 coins from a rewarded ad!',      timeAgo: '1h',  unread: true },
    { id: 'n3', type: 'streak',  body: 'Don\'t break your 5-day streak! Claim today.', timeAgo: '6h',  unread: false },
    { id: 'n4', type: 'system',  body: 'Welcome to vidashort! 50 coins are yours.',     timeAgo: '2d',  unread: false },
  ];

  // ============== Sponsored / Ads ==============
  const sponsored = {
    id: 'sp1',
    title: "The Forbidden Heir",
    subtitle: "Sponsored • Acme Co.",
    cover: TMDB.poster('forbiddenheir'),
    sponsor: 'Acme Co.',
    cta: 'Watch Now',
  };

  const bannerAd = {
    title: 'Install Acme VPN — Free for 7 days',
    cta: 'Install',
    pill: 'Sponsored',
  };

  // Rewarded ad creative (3 states: loading / playing / complete)
  const rewardedAd = {
    id: 'rw-acme-vpn',
    advertiser: 'Acme VPN',
    title: 'Acme VPN — Browse privately, stream anywhere',
    body: 'Watch this 15-second ad to earn 20 coins.',
    durationS: 15,
    rewardCoins: ECONOMY.adRewardCoins,
  };

  // Interstitial ad
  const interstitialAd = {
    id: 'is-the-forbidden-heir',
    title: "The Forbidden Heir",
    subtitle: 'Sponsored • Acme Studios',
    cover: TMDB.poster('forbiddenheir'),
    cta: 'Watch now',
    countdownS: 5,
  };

  // ============== User ==============
  const user = {
    name: 'Maya',
    username: '@maya_watches',
    email: 'maya@example.com',
    avatar: avatar('maya_user'),
    vip: false,
    coins: 120,                       // 120 coins = ₦12
    streak: 5,
    episodesWatched: 47,
    hoursWatched: 6.2,
    favoritesCount: 8,
    adsWatchedToday: 3,               // increments; resets daily
    adsWatchedOn: new Date().toISOString().slice(0, 10),  // YYYY-MM-DD; if mismatch, reset
    role: 'viewer',                   // 'viewer' | 'creator' | 'admin'
  };

  // ============== Settings menu ==============
  const settingsMenu = [
    { id: 'account',       label: 'Account',           icon: 'user-circle',   detail: user.email },
    { id: 'role',          label: 'Switch role',       icon: 'swap',          detail: user.role },
    { id: 'notifications', label: 'Notifications',     icon: 'bell',          detail: 'On' },
    { id: 'language',      label: 'Language',          icon: 'translate',     detail: 'English' },
    { id: 'downloads',     label: 'Downloads',         icon: 'download-simple', detail: 'Auto over Wi-Fi' },
    { id: 'playback',      label: 'Playback',          icon: 'play',          detail: 'Cellular quality' },
    { id: 'privacy',       label: 'Privacy & Data',    icon: 'shield-check' },
    { id: 'help',          label: 'Help & Support',    icon: 'question' },
    { id: 'terms',         label: 'Terms of Service',  icon: 'file-text' },
    { id: 'about',         label: 'About',             icon: 'info',          detail: 'v0.1.0 prototype' },
    { id: 'signout',       label: 'Sign Out',          icon: 'sign-out',      danger: true },
  ];

  // ===================================================================
  // CREATOR DATA
  // ===================================================================

  // Sample creator profiles (for browsing as a viewer + for the creator's own dashboard)
  const creators = [
    {
      id: 'cr1',
      handle: 'ada-stories',
      name: 'Ada Okafor',
      avatar: avatar('ada_creator'),
      bio: 'Lagos-based microdrama producer. CEO romances & family drama.',
      niche: 'CEO Romance',
      followers: 12800,
      totalViews: 1_240_000,
      seriesCount: 3,
      verified: true,
      joinedAt: '2025-09-12',
      payoutMethod: 'OPay',
      payoutAccount: '0813****7821',
      loyaltyPoints: 184500,           // earned 60% of paid unlocks
      lifetimeEarningsNaira: 18450,
      pendingPayoutNaira: 4500,
    },
    {
      id: 'cr2',
      handle: 'werehouse-ng',
      name: 'Kunle Adeyemi',
      avatar: avatar('werehouse'),
      bio: 'Werewolf / supernatural shorts. Lagos → Abuja → world.',
      niche: 'Werewolf',
      followers: 42100,
      totalViews: 4_800_000,
      seriesCount: 5,
      verified: true,
      joinedAt: '2025-04-03',
      payoutMethod: 'PalmPay',
      payoutAccount: '0701****0042',
      loyaltyPoints: 712000,
      lifetimeEarningsNaira: 71200,
      pendingPayoutNaira: 18200,
    },
  ];

  // Series uploaded by creators (separate from `series` originals).
  // Each creator series goes through a moderation state.
  const creatorSeries = [
    {
      id: 'cs1',
      creatorId: 'cr1',
      slug: 'my-boss-my-baby',
      title: 'My Boss, My Baby',
      synopsis: 'When her one-night stand turns out to be her new CEO, she has 9 months to figure out her next move.',
      cover: TMDB.poster('mybossmybaby'),
      backdrop: TMDB.poster('mybossmybaby', 'w1280'),
      language: 'en',
      region: 'WW',
      totalEpisodes: 12,
      isOriginal: false,
      isCreator: true,
      creatorId: 'cr1',
      copyrightOwner: 'ada-stories',
      category: 'Romance',
      tags: ['CEO', 'Romance', 'Pregnant', 'Workplace'],
      tmdbId: null,                   // creator uploads, not from TMDB
      moderationStatus: 'approved',   // 'pending' | 'approved' | 'rejected' | 'flagged'
      publishedAt: '2026-05-14',
      hot: true,
      views: 412300,
      rating: 4.5,
      episodes: [
        { number: 1,  title: 'The morning after',       durationS: 78, still: TMDB.still('mybossmybaby_e1'),  requiredCoins: 0, isFree: true,  isPaywalled: false, adPreroll: false, adMidroll: false },
        { number: 2,  title: 'His name on the door',    durationS: 80, still: TMDB.still('mybossmybaby_e2'),  requiredCoins: 0, isFree: true,  isPaywalled: false, adPreroll: false, adMidroll: false },
        { number: 3,  title: 'First meeting',           durationS: 75, still: TMDB.still('mybossmybaby_e3'),  requiredCoins: 0, isFree: true,  isPaywalled: false, adPreroll: false, adMidroll: false },
        { number: 4,  title: 'Two pink lines',          durationS: 82, still: TMDB.still('mybossmybaby_e4'),  requiredCoins: 0, isFree: true,  isPaywalled: false, adPreroll: false, adMidroll: false },
        { number: 5,  title: 'She almost quit',         durationS: 78, still: TMDB.still('mybossmybaby_e5'),  requiredCoins: 0, isFree: true,  isPaywalled: false, adPreroll: false, adMidroll: false },
        { number: 6,  title: 'He notices',              durationS: 85, still: TMDB.still('mybossmybaby_e6'),  requiredCoins: ECONOMY.episodeCostCoins, isFree: false, isPaywalled: true, adPreroll: true, adMidroll: true },
        { number: 7,  title: 'The boardroom',           durationS: 80, still: TMDB.still('mybossmybaby_e7'),  requiredCoins: ECONOMY.episodeCostCoins, isFree: false, isPaywalled: true, adPreroll: true, adMidroll: false },
        { number: 8,  title: 'Her secret',              durationS: 88, still: TMDB.still('mybossmybaby_e8'),  requiredCoins: ECONOMY.episodeCostCoins, isFree: false, isPaywalled: true, adPreroll: true, adMidroll: true },
        { number: 9,  title: 'A public proposal',       durationS: 82, still: TMDB.still('mybossmybaby_e9'),  requiredCoins: ECONOMY.episodeCostCoins, isFree: false, isPaywalled: true, adPreroll: true, adMidroll: false },
        { number: 10, title: 'The truth comes out',     durationS: 90, still: TMDB.still('mybossmybaby_e10'), requiredCoins: ECONOMY.episodeCostCoins, isFree: false, isPaywalled: true, adPreroll: true, adMidroll: true },
        { number: 11, title: 'A choice',                durationS: 78, still: TMDB.still('mybossmybaby_e11'), requiredCoins: ECONOMY.episodeCostCoins, isFree: false, isPaywalled: true, adPreroll: true, adMidroll: false },
        { number: 12, title: 'Happily ever after',      durationS: 92, still: TMDB.still('mybossmybaby_e12'), requiredCoins: ECONOMY.episodeCostCoins, isFree: false, isPaywalled: true, adPreroll: true, adMidroll: true },
      ],
    },
    {
      id: 'cs2',
      creatorId: 'cr2',
      slug: 'moonbound',
      title: 'Moonbound',
      synopsis: 'A rejected omega returns to the pack three years later — but the moon has other plans for her.',
      cover: TMDB.poster('moonbound'),
      backdrop: TMDB.poster('moonbound', 'w1280'),
      language: 'en',
      region: 'WW',
      totalEpisodes: 8,
      isOriginal: false,
      isCreator: true,
      creatorId: 'cr2',
      copyrightOwner: 'werehouse-ng',
      category: 'Werewolf',
      tags: ['Werewolf', 'Romance', 'Revenge'],
      tmdbId: null,
      moderationStatus: 'pending',   // in admin moderation queue
      publishedAt: null,
      hot: false,
      views: 0,
      rating: 0,
      episodes: [
        { number: 1, title: 'The exile',            durationS: 78, still: TMDB.still('moonbound_e1'), requiredCoins: 0, isFree: true,  isPaywalled: false, adPreroll: false, adMidroll: false },
        { number: 2, title: 'Three winters',        durationS: 80, still: TMDB.still('moonbound_e2'), requiredCoins: 0, isFree: true,  isPaywalled: false, adPreroll: false, adMidroll: false },
        { number: 3, title: 'The blood moon',       durationS: 75, still: TMDB.still('moonbound_e3'), requiredCoins: 0, isFree: true,  isPaywalled: false, adPreroll: false, adMidroll: false },
        { number: 4, title: 'The pack',             durationS: 82, still: TMDB.still('moonbound_e4'), requiredCoins: 0, isFree: true,  isPaywalled: false, adPreroll: false, adMidroll: false },
        { number: 5, title: 'He returns',           durationS: 78, still: TMDB.still('moonbound_e5'), requiredCoins: 0, isFree: true,  isPaywalled: false, adPreroll: false, adMidroll: false },
        { number: 6, title: 'The first howl',       durationS: 85, still: TMDB.still('moonbound_e6'), requiredCoins: ECONOMY.episodeCostCoins, isFree: false, isPaywalled: true, adPreroll: true, adMidroll: true },
        { number: 7, title: 'Claimed',              durationS: 80, still: TMDB.still('moonbound_e7'), requiredCoins: ECONOMY.episodeCostCoins, isFree: false, isPaywalled: true, adPreroll: true, adMidroll: false },
        { number: 8, title: 'Moonbound',            durationS: 88, still: TMDB.still('moonbound_e8'), requiredCoins: ECONOMY.episodeCostCoins, isFree: false, isPaywalled: true, adPreroll: true, adMidroll: true },
      ],
    },
  ];

  // All discoverable series (originals + approved creator uploads)
  const allSeries = [
    ...series,
    ...creatorSeries.filter((s) => s.moderationStatus === 'approved'),
  ];

  // All episodes for the home feed (originals + approved creator)
  const allFeedEpisodes = allSeries.flatMap((s) =>
    s.episodes.map((e) => ({
      ...e,
      seriesId: s.id,
      seriesTitle: s.title,
      seriesCover: s.cover,
      seriesSlug: s.slug,
      category: s.category,
      isCreator: !!s.isCreator,
      creatorId: s.creatorId,
    }))
  );

  // Creator analytics (sample 30-day window)
  const creatorAnalytics = {
    'cr1': {
      rangeDays: 30,
      views: 412300,
      unlocks: 18420,                 // paid episode unlocks
      coinsEarned: 460500,            // 60% of paid unlocks
      nairaEarned: 46050,             // ÷10
      adRevenueShare: 8200,           // bonus from ad views on their content
      seriesBreakdown: [
        { seriesId: 'cs1', title: 'My Boss, My Baby',     views: 412300, unlocks: 18420, earnings: 46050 },
      ],
      dailyViews: Array.from({ length: 30 }, (_, i) => ({ day: i, views: 8000 + Math.round(Math.random() * 14000) })),
    },
  };

  // Payout requests (pending / approved / paid)
  const payoutRequests = [
    { id: 'po1', creatorId: 'cr1', amountCoins: 184500, amountNaira: 18450, status: 'pending',  requestedAt: '2026-07-18', method: 'OPay',   account: '0813****7821' },
    { id: 'po2', creatorId: 'cr2', amountCoins: 712000, amountNaira: 71200, status: 'approved', requestedAt: '2026-07-15', method: 'PalmPay', account: '0701****0042' },
    { id: 'po3', creatorId: 'cr1', amountCoins:  90000, amountNaira:  9000, status: 'paid',     requestedAt: '2026-07-01', method: 'OPay',   account: '0813****7821' },
  ];

  // ===================================================================
  // ADMIN DATA
  // ===================================================================

  // Moderation queue (series + episodes + comments + accounts awaiting review)
  const moderationQueue = {
    series: [
      { id: 'mod-s1', type: 'series',  refId: 'cs2',            title: 'Moonbound',                   submitter: 'werehouse-ng',  submittedAt: '2026-07-20', reason: 'New series awaiting first review', priority: 'normal' },
      { id: 'mod-s2', type: 'series',  refId: 'cs-pending-2',   title: 'Married to the Mafia Don',    submitter: 'violet-cree',   submittedAt: '2026-07-19', reason: 'AI flag: suggestive thumbnail',      priority: 'high' },
      { id: 'mod-s3', type: 'series',  refId: 'cs-pending-3',   title: 'Bound by Blood',              submitter: 'kobo-stories',  submittedAt: '2026-07-19', reason: 'AI flag: violence in trailer',       priority: 'normal' },
    ],
    comments: [
      { id: 'mod-c1', type: 'comment', refId: 'c-mod-1',        author: 'spam_bot_9001',   snippet: 'Check my bio for free coins!!! 😍😍😍',          reportedAt: '2026-07-21', reason: 'Spam',         priority: 'normal' },
      { id: 'mod-c2', type: 'comment', refId: 'c-mod-2',        author: 'angry_viewer',    snippet: 'this is so dumb, you people are idiots',         reportedAt: '2026-07-21', reason: 'Abuse',        priority: 'normal' },
    ],
    accounts: [
      { id: 'mod-a1', type: 'account', refId: 'u-mod-1',        handle: 'free_coins_daily', reportedAt: '2026-07-20', reason: 'Suspected bot / promo abuse', priority: 'high' },
    ],
  };

  // Admin overview KPIs
  const adminKpis = {
    range: 'Last 7 days',
    dau: 184230,
    mau: 612000,
    newSignups: 28420,
    paidUsers: 41200,
    vipActive: 18400,
    gmvNaira: 12480000,            // gross merchandise value
    platformRevenueNaira: 4992000, // 40% of GMV (GMV here = paid unlocks + packs + VIP)
    creatorPayoutsNaira: 7488000,  // 60% of GMV
    adsServed: 2_400_000,
    adRevenueNaira: 1_840_000,
    coinStoreRevenueNaira: 8_200_000,
    vipRevenueNaira: 1_240_000,
    adCapHits: 1840,               // users who hit the 100-ad cap today
    averageSessionMinutes: 42,
    retentionD1: 0.38,
    retentionD7: 0.18,
  };

  // Admin → user list (manage users)
  const adminUsers = [
    { id: 'u1', name: 'Maya Okafor',     email: 'maya@example.com',  role: 'viewer',  coins: 120,    vip: false, country: 'NG', joinedAt: '2026-07-10', status: 'active',    spendNaira: 0 },
    { id: 'u2', name: 'Tunde Bello',      email: 'tunde@example.com', role: 'viewer',  coins: 1450,   vip: true,  country: 'NG', joinedAt: '2026-05-04', status: 'active',    spendNaira: 22000 },
    { id: 'u3', name: 'Ada Okafor',       email: 'ada@example.com',   role: 'creator', coins: 0,      vip: false, country: 'NG', joinedAt: '2025-09-12', status: 'active',    spendNaira: 0, earningsNaira: 18450 },
    { id: 'u4', name: 'Kunle Adeyemi',    email: 'kunle@example.com', role: 'creator', coins: 0,      vip: false, country: 'NG', joinedAt: '2025-04-03', status: 'active',    spendNaira: 0, earningsNaira: 71200 },
    { id: 'u5', name: 'Spam Bot 9001',    email: 'spam@bot.com',      role: 'viewer',  coins: 5000,   vip: false, country: 'XX', joinedAt: '2026-07-20', status: 'flagged',   spendNaira: 0 },
  ];

  // Admin → ad management (active campaigns)
  const adCampaigns = [
    { id: 'ad1', advertiser: 'Acme VPN',         type: 'rewarded',   status: 'active',   dailyCap: 200000, delivered: 184230, payoutNairaPerView: 2.0,  startDate: '2026-07-01', endDate: '2026-07-31' },
    { id: 'ad2', advertiser: 'Acme Studios',     type: 'interstitial', status: 'active', dailyCap: 500000, delivered: 412000, payoutNairaPerView: 1.5,  startDate: '2026-07-10', endDate: '2026-08-10' },
    { id: 'ad3', advertiser: 'OPay',            type: 'banner',      status: 'active',   dailyCap: null,   delivered: 1240000, payoutNairaPerView: 0.6,  startDate: '2026-06-15', endDate: '2026-09-15' },
    { id: 'ad4', advertiser: 'PalmPay',         type: 'banner',      status: 'paused',   dailyCap: null,   delivered: 0,       payoutNairaPerView: 0.6,  startDate: '2026-07-20', endDate: '2026-08-20' },
  ];

  // Admin → financial ledger (reconciliation view)
  const adminLedger = [
    { id: 'l1', date: '2026-07-22', type: 'coin_pack',  refId: 'coins_220',  grossNaira: 2000,   platformNaira: 800,  creatorNaira: 0,    adNaira: 0,   ref: 'Maya Okafor' },
    { id: 'l2', date: '2026-07-22', type: 'unlock',     refId: 'cs1-6',      grossNaira: 25,     platformNaira: 10,   creatorNaira: 15,   adNaira: 0,   ref: 'Tunde Bello → ada-stories' },
    { id: 'l3', date: '2026-07-22', type: 'rewarded_ad',refId: 'rw-acme-vpn',grossNaira: 0,      platformNaira: 0,    creatorNaira: 0,    adNaira: 2,   ref: 'Acme VPN (payout to vidashort)' },
    { id: 'l4', date: '2026-07-22', type: 'vip',        refId: 'vip_monthly',grossNaira: 2000,   platformNaira: 2000, creatorNaira: 0,    adNaira: 0,   ref: 'Tunde Bello' },
    { id: 'l5', date: '2026-07-22', type: 'creator_payout', refId: 'po2',    grossNaira: -71200, platformNaira: -71200, creatorNaira: 0,  adNaira: 0,   ref: 'werehouse-ng payout' },
  ];

  // ============== Public API ==============
  window.vidashort = window.vidashort || {};
  window.vidashort.MockData = {
    ECONOMY,
    TMDB,
    series, allEpisodes,
    creatorSeries, allSeries, allFeedEpisodes,
    coinPacks,
    vipPlans,
    genres,
    trendingTags,
    sampleComments,
    sampleNotifications,
    sponsored, bannerAd, rewardedAd, interstitialAd,
    user,
    settingsMenu,
    creators,
    creatorAnalytics,
    payoutRequests,
    moderationQueue,
    adminKpis,
    adminUsers,
    adCampaigns,
    adminLedger,
    // Helpers
    getSeriesBySlug(slug) { return allSeries.find((s) => s.slug === slug); },
    getSeriesById(id) { return allSeries.find((s) => s.id === id); },
    getEpisodeById(seriesId, epNumber) {
      const s = allSeries.find((x) => x.id === seriesId);
      return s ? s.episodes.find((e) => e.number === epNumber) : null;
    },
    getNextEpisode(seriesId, epNumber) {
      const s = allSeries.find((x) => x.id === seriesId);
      if (!s) return null;
      const next = s.episodes.find((e) => e.number === epNumber + 1);
      if (next) return { ...next, seriesId: s.id, seriesTitle: s.title, seriesCover: s.cover, seriesSlug: s.slug };
      // Loop to first episode of next series
      const idx = allSeries.indexOf(s);
      const nextSeries = allSeries[(idx + 1) % allSeries.length];
      const first = nextSeries.episodes[0];
      return { ...first, seriesId: nextSeries.id, seriesTitle: nextSeries.title, seriesCover: nextSeries.cover, seriesSlug: nextSeries.slug };
    },
    getCreatorById(id) { return creators.find((c) => c.id === id); },
    getSeriesByCreator(creatorId) { return [...series, ...creatorSeries].filter((s) => s.creatorId === creatorId); },
  };
})();

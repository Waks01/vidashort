# Cover images

This prototype uses **seeded picsum.photos URLs** for all placeholder cover art:

```
https://picsum.photos/seed/{slug}/540/960
```

The seed is a stable string (e.g. series slug). The same seed always returns the same
image, so reloading the page produces consistent mockups.

When you acquire real licensed cover art, drop the files here and update
`scripts/data.js` to reference them, e.g.:

```js
cover: './assets/images/ceos-secret-heir.jpg'
```

The home feed, series detail, player, and discover grid all use these covers.

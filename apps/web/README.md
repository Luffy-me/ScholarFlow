# ScholarFlow Web

Production UI for ScholarFlow. Consumes the existing FastAPI backend; does not rewrite agents.

See `docs/UI.md` in the repo root for architecture, routes, and shortcuts.
See `docs/PREMIUM_UX.md` for Phase 11 streaming UX and keyboard map.

```bash
npm install
npm run dev
```

Requires the API on `http://127.0.0.1:8000` (override with `SCHOLARFLOW_API_URL`).

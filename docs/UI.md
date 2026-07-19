# ScholarFlow UI

Premium desktop-style frontend for the completed ScholarFlow backend.

## Stack

Next.js 15 · React 19 · TypeScript · Tailwind CSS v4 · Radix/shadcn-style primitives · Framer Motion · TanStack Query · React Hook Form · Zod · Lucide · Monaco · React Flow · Recharts

## Location

`apps/web`

## Run

```bash
# terminal 1 — API (repo root)
uvicorn apps.api.main:app --reload --port 8000

# terminal 2 — UI
cd apps/web
npm install
npm run dev
```

Open `http://localhost:3000`.

Proxy: browser calls `/backend/*` → `SCHOLARFLOW_API_URL` (default `http://127.0.0.1:8000`).

## Architecture

```text
Sidebar · Top Nav · Main Workspace · Inspector · Status Bar
```

Pages consume **existing FastAPI routes** only:

| UI | Backend |
|---|---|
| Dashboard / History / Output | `GET/PATCH /api/v1/posts` |
| Generate | `POST /api/v1/generate` |
| Research (from last run) | generate `research` / `insight` / `content_opportunity` |
| Settings models/status/memory | `/api/v1/ai/*`, `/api/v1/memory` |
| Evidence on a post | `/api/v1/posts/{id}/evidence` |

Read-only UI adapters (do **not** modify agents):

| Adapter | Purpose |
|---|---|
| `GET /api/local/knowledge/graph` | Reads `knowledge_graph/graph.json` |
| `GET /api/local/knowledge/evidence` | Reads evidence graph JSON |
| `POST /api/local/carousel` | Invokes existing `carousel.pipeline` via Python subprocess |

## Shortcuts

- `⌘K` / `⌘/` — Command palette
- `⌘Enter` — Generate
- `⌘S` — Save output

## Design

White / gray / black with blue accent, optional dark mode, large spacing, soft shadows, no decorative gradients.

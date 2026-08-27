# Frontend – Chinese Learning Platform

React 19 + TypeScript + Vite + Tailwind CSS 4 UI for the Chinese vocabulary training platform.

## Stack

| Piece         | Choice                               |
| ------------- | ------------------------------------ |
| Framework     | React 19 + TypeScript                |
| Build         | Vite 8                               |
| Styling       | Tailwind CSS 4 (`@tailwindcss/vite`) |
| Data fetching | TanStack Query + Axios               |
| Icons         | lucide-react                         |

## Local development

### Prerequisites

- Node.js 20+ (22 recommended; matches CI)
- Backend API running on `http://localhost:8000` (see root [README](../README.md))

### Setup

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server runs on **port 3000** and proxies `/api/*` to `http://localhost:8000` (see `vite.config.ts`). You do not need to change the Axios base URL for local work.

### Scripts

| Command           | Description                             |
| ----------------- | --------------------------------------- |
| `npm run dev`     | Dev server with HMR                     |
| `npm run build`   | Typecheck (`tsc -b`) + production build |
| `npm run lint`    | ESLint                                  |
| `npm run preview` | Preview the production build            |

### Full stack via Docker

From the **repository root**:

```bash
docker compose up --build
```

| Service          | URL                        |
| ---------------- | -------------------------- |
| Frontend (nginx) | http://localhost:3000      |
| Backend API      | http://localhost:8000      |
| Swagger          | http://localhost:8000/docs |

In Docker, nginx proxies `/api/` to the `backend` service (see `nginx.conf`).

## Layout

```
src/
├── api/           # Thin Axios wrappers per domain (text import, practice, dashboards, …)
├── components/    # Feature views
├── App.tsx        # Tab shell / navigation
└── …
```

API calls use `src/api/client.ts` (`baseURL: "/api/v1"`). Paths are relative so the same client works under Vite proxy and under nginx in Docker.

## Notes

- Prefer feature-level components under `components/` and keep HTTP in `api/`.
- Keep the Vite proxy and nginx `/api/` proxy in sync if you change API routing.
- CI runs `npm ci`, `npm run lint`, and `npm run build` on every PR (see `.github/workflows/ci.yml`).

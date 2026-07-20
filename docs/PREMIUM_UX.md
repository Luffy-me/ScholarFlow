# Phase 11 — Premium UX

ScholarFlow’s web app (`apps/web`) uses **client-side progressive reveal** for a streaming feel. The backend `POST /api/v1/generate` response is unchanged (single JSON payload).

## Streaming pipeline

1. **Generate** starts the API call and shows live pipeline + thinking timeline.
2. When the response arrives, `replayGenerationResult` feeds the UI incrementally:
   - Research sources → evidence → summary
   - Reasoning sections (from `insight`, `strategy`, `angles`)
   - Draft paragraphs
   - Optimization / editorial milestones
   - Optional carousel via existing `/api/local/carousel` adapter
3. State lives in Zustand (`useWorkflowStore`) and persists key artifacts.

## Keyboard & command palette

| Shortcut | Action |
|----------|--------|
| ⌘K / `/` | Command palette |
| ⌘↵ | Generate (on Generate page) |
| ⌘S | Download markdown |
| ⌘⇧C | Copy LinkedIn |
| Esc | Close command palette |

## Components

- `ThinkingTimeline` — milestones with timestamps
- `LiveResearchPanel` / `LiveReasoningPanel`
- `StreamingPost` — paragraph reveal
- `VersionTimeline` — v1 → optimization → editorial → final compare
- `ErrorRetry` — retry from failed replay stage when result is cached
- `VirtualList` — history post list
- `ExportActions` — copy/download actions

## Performance

- `@tanstack/react-virtual` for long history lists
- Dynamic import for Monaco on Output
- Memo-friendly presentational components; generation replay uses timed chunks to keep the main thread responsive

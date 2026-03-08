# Frontend integration guide — lovable.ai

This document explains how to build a frontend for this project that integrates with lovable.ai for embeddings/RAG/QA and with the existing backend assets in this repository.

## Overview

- Purpose: Provide a concise, copy-pasteable guide for frontend developers to connect a UI to the project's backend and lovable.ai services.
- Location: Use this file alongside the code in [Phase2](Phase2).

## Prerequisites

- Node.js >=16 and `npm` or `pnpm`/`yarn`
- Access to a lovable.ai API key (or equivalent service keys)
- Backend running on a known host (local or deployed)

## Project files to inspect

- Backend / data generators: [Phase2/Knowledge_graph/Train/deed_entity_annotator.py](Phase2/Knowledge_graph/Train/deed_entity_annotator.py)
- Deed data / processed JSON: [Phase2/Knowledge_graph/data/deeds/processed](Phase2/Knowledge_graph/data/deeds/processed)
- Phase2 API folder (if present) for HTTP endpoints: [Phase2/API](Phase2/API)

Review these to learn request shapes and available endpoints before wiring the frontend.

## Architecture and flow

1. Frontend sends user queries (search / chat / annotation) to a backend API.
2. Backend handles ingestion, retrieval, embeddings and/or forwards to lovable.ai where needed.
3. Backend returns results (documents, passages, answer + provenance, structured entities) to the frontend.
4. Frontend displays results, highlights provenance, and lets the user annotate or follow-up.

The frontend should be primarily a thin client; heavyweight embedding and RAG steps belong on server-side.

## Recommended API contracts (suggested)

Note: adapt to the real endpoints in [Phase2/API](Phase2/API) or your backend. These are example contracts to implement if missing.

- POST /api/search
  - Request: `{ "query": "text", "top_k": 5 }`
  - Response: `{ "results": [{ "id":"DEED_001","score":0.92,"snippet":"...","source":"DEED_001.json","cursor":{...} }] }`

- POST /api/qa
  - Request: `{ "query": "text", "context_ids": ["DEED_001"], "chat_history": [] }`
  - Response: `{ "answer":"...","provenance":[ {"id":"DEED_001","offsets":[[12,220]] } ], "sources": [...] }

- GET /api/deed/:id
  - Response: full deed JSON with structured fields and full text.

- POST /api/annotate
  - Request: `{ "id": "DEED_001", "annotations": {...}, "user": "alice" }`

## lovable.ai integration patterns

Two integration models are common:

1. Backend-first (recommended)
   - Backend owns the lovable.ai API key and calls lovable.ai for embeddings, retrieval, and LLM prompts.
   - Frontend never sees the key; it only talks to backend endpoints above.

2. Direct-from-frontend (only for prototypes)
   - Frontend holds a short-lived key via a secure session/token service.
   - Not recommended for production.

Example ingestion flow (backend):

- Upload deed text or select existing deed
- Backend sends text to lovable.ai to create embeddings and store vectors in DB/vector store
- Backend updates metadata and exposes search endpoints

Example QA flow (backend):

- Frontend POST /api/qa -> backend
- Backend retrieves top_k contexts (vector search via lovable.ai or vector DB), assembles prompt
- Backend calls lovable.ai's LLM endpoint with prompt and returns answer + provenance

## Frontend components & UI patterns

- Search bar: simple input calling `/api/search`.
- Results list: show score, short snippet, and a `View` action.
- Document viewer: render structured deed JSON, full text, and highlight provenance spans returned by `/api/qa`.
- Chat panel: incremental Q/A — maintain chat history and call `/api/qa` with `chat_history`.
- Annotation editor: allow tagging entities and sending to `/api/annotate`.
- Graph view: an optional knowledge graph visualization from structured entities (use D3 or Cytoscape).

UX notes:

- Always show provenance links (document + offset) for answers.
- Provide "Cite source", "Follow-up question", `Open document` buttons.

## Example frontend request (fetch)

```js
// Search
const res = await fetch('/api/search', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query: 'What is the registered owner?' })
});
const data = await res.json();

// QA
const qa = await fetch('/api/qa', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query: 'Who is the seller?', context_ids: [data.results[0].id] })
}).then(r=>r.json());
```

## Environment variables and secrets

- LOVABLE_API_KEY: (backend-only) lovable.ai API key
- BACKEND_URL: frontend will call this if not proxied (e.g., `http://localhost:8000`)

Store secrets on the server; never expose them in frontend bundles.

## Local dev & run

1. Start backend (see [Phase2/API](Phase2/API) for specifics).
2. Create a simple React app (Vite or CRA) and set `VITE_BACKEND_URL` or use relative paths.

Commands (example):

```bash
# create app
pnpm create vite frontend --template react
cd frontend
pnpm install
pnpm dev
```

Set `VITE_BACKEND_URL=http://localhost:8000` in `.env` for the frontend.

## Deployment

- Host frontend on Vercel/Netlify or any static host.
- Ensure CORS and secure cookies are configured on backend.
- Backend should run in a server environment with `LOVABLE_API_KEY` set.

## Examples & quick copyables

- Quick UI sketch: Search -> Results -> Open -> Ask follow-up -> Show provenance
- Minimal React hook for search:

```js
import { useState } from 'react';
export function useSearch() {
  const [results, setResults] = useState([]);
  async function search(q){
    const r = await fetch('/api/search',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({query:q})});
    setResults(await r.json());
  }
  return { results, search };
}
```

## Next steps / checklist

- Implement backend endpoints if missing in [Phase2/API](Phase2/API).
- Scaffold frontend (Vite + React) and wire `Search`, `Document`, and `Chat` pages.
- Add unit/e2e tests for critical interactions (search -> view -> QA).

If you want, I can scaffold a starter React app with example pages and components wired to these endpoints.

---
Generated: Frontend guide to integrate this project with lovable.ai. Ask me to scaffold the starter frontend next.

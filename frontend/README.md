# ClauseGuard frontend

React + Vite + React Query. Talks to the Django API at `VITE_API_URL`
(default `http://localhost:8001`).

## Local dev without Docker

```bash
npm install
cp .env.example .env
npm run dev
```

Open http://localhost:5174 (the backend must be running separately, see
../backend/README.md).

## Structure

- `src/api/client.js` -- axios instance + error-message helper
- `src/api/hooks.js` -- React Query hooks: `useContracts`, `useContract`,
  `usePlaybook`, `useUploadContract`
- `src/components/` -- `UploadForm`, `ContractList`, `ReviewReport`,
  `ClauseFindingCard`, `RiskBadge`

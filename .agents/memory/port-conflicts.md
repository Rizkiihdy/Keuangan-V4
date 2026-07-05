---
name: Port conflicts
description: Which ports are already taken in this Replit environment
---

## Occupied Ports

- **8080** — Express API server (`artifacts/api-server`), always running
- **8081** — Mockup sandbox (`artifacts/mockup-sandbox`)
- **5000** — Replit webview port (Vite dashboard)
- **3001** — Flask Dashboard API (`dashboard_api.py`)

## Why
The Express API server binds to 8080 on startup. Trying to start any other service on 8080 causes "Address already in use" and workflow failure.

## How to apply
When adding a new service, pick from: 3000, 3002, 3003, 6000, 8000, 9000. Never 8080 or 8081.

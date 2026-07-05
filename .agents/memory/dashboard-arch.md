---
name: Dashboard architecture
description: How the Oliv financial dashboard is structured — ports, services, and data flow
---

## Architecture

- **Flask API** (`dashboard_api.py`): port 3001, outputType console. Reads all Google Sheets and returns clean JSON.
- **Vite React Dashboard** (`dashboard/`): port 5000, outputType webview. Proxies `/api/*` → Flask 3001.
- **Telegram Bot** (`python main.py`): no HTTP port, runs as console workflow.
- **Express API** (`artifacts/api-server`): port 8080 — do NOT use this port for anything else.

## Why port 3001 for Flask
Port 8080 is taken by the Express artifacts/api-server. Port 5000 is reserved for Replit webview (Vite dashboard). 3001 is safe.

## How to apply
Any new backend service: avoid 8080 and 5000. Use 3001, 3002, 3003, 6000, 8000, etc.

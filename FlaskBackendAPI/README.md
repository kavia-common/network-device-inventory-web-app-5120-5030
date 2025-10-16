# Flask Backend API - Network Device Inventory

This backend provides RESTful endpoints for managing devices and their status.

## Ports
- Flask Backend: 3001
- MongoDB: 5001
- React Frontend: 3000

## Environment Variables

Create `.env` from `.env.example` and set:

- API_KEY: Optional shared key expected in header X-API-KEY
- MONGODB_URI: e.g., mongodb://localhost:5001
- MONGODB_DB_NAME: device_inventory
- MONGODB_COLLECTION_DEVICES: devices
- MONGODB_COLLECTION_LOGS: logs
- PYTHONPING_ENABLED: true/false
- FLASK_RUN_PORT: 3001
- CORS_ALLOWED_ORIGINS: http://localhost:3000

If API_KEY is set, ensure the frontend sets REACT_APP_API_KEY with the same value.

## Startup Order (local)
1. Start MongoDB on port 5001
2. Start Flask Backend on port 3001
3. Start React Frontend on port 3000

## API Docs
OpenAPI/Swagger UI is available at /docs and the OpenAPI JSON at /openapi.json.

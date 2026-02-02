# ATM-RDC - Air Traffic Management System for the Democratic Republic of Congo

## Overview

ATM-RDC is a comprehensive web-based air traffic management system developed for the Régie des Voies Aériennes (RVA) of the Democratic Republic of Congo. The system provides real-time flight tracking, overflight detection with geofencing, automated billing, and administrative tools.

## Technology Stack

- **Backend**: Python 3.11+ with Flask Framework
- **Async Processing**: Celery + Redis (for processing API data flows without blocking the UI)
- **WebSockets**: Flask-SocketIO (for real-time radar data push to browser)
- **Database**: PostgreSQL 15+ with PostGIS extension (for geospatial calculations)
- **Frontend**: HTML5 / JavaScript ES6 Modules / Tailwind CSS
- **Mapping**: Leaflet.js (open source cartographic engine)
- **PDF Generation**: ReportLab

## Project Structure

```
├── algorithms/        # Custom algorithms (geofencing, route calculation)
├── config/           # Configuration files
│   └── settings.py   # Flask and database configuration
├── docs/             # Documentation
├── lang/             # Localization files (French)
├── models/           # SQLAlchemy models
│   └── __init__.py   # All database models
├── routes/           # Flask blueprints
│   ├── auth.py       # Authentication routes
│   ├── dashboard.py  # Dashboard routes
│   ├── radar.py      # Live radar, overflights, terminal
│   ├── flights.py    # Flight management
│   ├── invoices.py   # Billing system
│   ├── admin.py      # Administration
│   └── api.py        # REST API endpoints
├── scripts/          # Utility scripts
├── security/         # Security utilities
├── services/         # Business logic services
│   ├── flight_tracker.py    # Real-time flight tracking
│   └── invoice_generator.py # PDF invoice generation
├── statics/          # Static files (CSS, JS, images)
├── tasks/            # Celery async tasks
│   ├── flight_tasks.py      # Flight position fetching
│   └── invoice_tasks.py     # Invoice generation tasks
├── templates/        # Jinja2 HTML templates
├── utils/            # Utility modules
│   ├── decorators.py # Role-based access decorators
│   └── helpers.py    # Helper functions
├── app.py            # Main Flask application
├── celery_app.py     # Celery configuration
├── init_db.py        # Database initialization script
└── python_requirements.txt # Python dependencies
```

## Running the Application

The application runs via the workflow:
```bash
npm run dev  # Executes: python app.py
```

The Flask server runs on `http://0.0.0.0:5000`

### Starting Celery Worker (for async tasks)
```bash
celery -A celery_app worker --loglevel=info
```

### Starting Celery Beat (for scheduled tasks)
```bash
celery -A celery_app beat --loglevel=info
```

## Database Initialization

Run the database initialization script to create tables and seed data:
```bash
python init_db.py
```

## Environment Variables

Configure these in your `.env` file or Replit Secrets:

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes (auto-configured) |
| `SESSION_SECRET` | Flask session secret key | Yes |
| `REDIS_URL` | Redis connection for Celery | Optional |
| `FLIGHT_API_KEY` | External flight data API key | Optional |
| `FLIGHT_API_URL` | External flight data API URL | Optional |

## Default User Accounts

| Username | Password | Role |
|----------|----------|------|
| admin | password123 | SuperAdmin |
| supervisor_kin | password123 | Supervisor |
| controller1 | password123 | Controller |
| billing | password123 | Billing |
| auditor | password123 | Auditor |

**Note:** Change these default passwords in production!

## Key Features

### 1. Live Radar (`/radar`)
- Real-time aircraft tracking on Leaflet.js map
- RDC airspace boundary visualization
- Flight status filtering and search
- WebSocket updates for live positions

### 2. Overflight Tracking (`/radar/overflights`)
- Automatic detection of aircraft entering RDC airspace
- Geofencing using Shapely/PostGIS for "Point in Polygon" calculations
- Entry/exit point recording with timestamps
- Distance and duration calculation

### 3. ATM Terminal (`/radar/terminal`)
- Inbound flight monitoring
- Aircraft on ground tracking
- Airport status overview

### 4. Billing System (`/invoices`)
- Automated invoice generation from overflights and landings
- PDF export with ReportLab
- Configurable tariffs
- Payment status tracking

### 5. Administration (`/admin`)
- User management with RBAC
- Airline and aircraft database
- Airport configuration
- Audit logs for compliance

## Role-Based Access Control (RBAC)

| Role | Permissions |
|------|-------------|
| superadmin | Full system access |
| supervisor | Operations management |
| controller | Flight tracking and monitoring |
| billing | Invoice and tariff management |
| auditor | Read-only access to all modules + audit logs |
| observer | Read-only dashboard access |

## API Endpoints

### Authentication
- `POST /auth/login` - User login
- `GET /auth/logout` - User logout

### Radar API
- `GET /radar/api/flights` - Active flights
- `GET /radar/api/boundary` - RDC boundary GeoJSON
- `GET /radar/api/alerts` - Active alerts
- `GET /radar/api/airports` - Domestic airports

### Flights API
- `GET /api/flights` - List flights
- `GET /api/flights/<id>` - Flight details
- `GET /api/overflights` - Overflight sessions

## Celery Tasks

### Periodic Tasks (via Celery Beat)
- `fetch_flight_positions` - Every 5 seconds
- `check_airspace_entries` - Every 10 seconds
- `generate_pending_invoices` - Every hour

### On-demand Tasks
- `process_flight_data` - Process incoming flight data
- `generate_single_invoice` - Generate specific invoice
- `send_invoice_notification` - Send invoice notification

## Recent Changes

- **2026-02-02**: Initial system deployment
  - Full Python/Flask backend implementation
  - PostgreSQL database with all models
  - Real-time radar with Leaflet.js
  - Automated billing system with PDF generation
  - RBAC with audit logging
  - Celery + Redis integration for async processing

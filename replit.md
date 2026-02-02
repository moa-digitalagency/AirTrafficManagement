# ATM-RDC - Air Traffic Management System for the Democratic Republic of Congo

## Overview

ATM-RDC is a comprehensive web-based air traffic management system developed for the Régie des Voies Aériennes (RVA) of the Democratic Republic of Congo. The system provides real-time flight tracking, overflight detection with geofencing, automated billing, and administrative tools.

## Technology Stack

- **Backend**: Python 3.11+ / Flask with SQLAlchemy ORM
- **Database**: PostgreSQL with PostGIS extensions
- **Real-time**: Flask-SocketIO for WebSocket communication
- **Frontend**: HTML5 / Tailwind CSS / Leaflet.js for mapping
- **PDF Generation**: ReportLab for invoice generation

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
├── templates/        # Jinja2 HTML templates
├── utils/            # Utility modules
│   ├── decorators.py # Role-based access decorators
│   └── helpers.py    # Helper functions
├── app.py            # Main Flask application
├── init_db.py        # Database initialization script
└── python_requirements.txt # Python dependencies
```

## Running the Application

The application runs via the workflow which executes:
```bash
npm run dev  # This spawns: python app.py
```

The Flask server runs on `http://0.0.0.0:5000`

## Database Initialization

Run the database initialization script to create tables and seed data:
```bash
python init_db.py
```

## Default User Accounts

| Username | Password | Role |
|----------|----------|------|
| admin | password123 | SuperAdmin |
| supervisor_kin | password123 | Supervisor |
| controller1 | password123 | Controller |
| billing | password123 | Billing |
| auditor | password123 | Auditor |

## Key Features

### 1. Live Radar (`/radar`)
- Real-time aircraft tracking on Leaflet.js map
- RDC airspace boundary visualization
- Flight status filtering and search
- WebSocket updates for live positions

### 2. Overflight Tracking (`/radar/overflights`)
- Automatic detection of aircraft entering RDC airspace
- Geofencing using Shapely library
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

### Flights API
- `GET /api/flights` - List flights
- `GET /api/flights/<id>` - Flight details
- `GET /api/overflights` - Overflight sessions

## Environment Variables

- `DATABASE_URL` - PostgreSQL connection string (auto-configured)
- `SESSION_SECRET` - Flask session secret key
- `PORT` - Server port (default: 5000)

## Recent Changes

- **2026-02-02**: Initial system deployment
  - Full Python/Flask backend implementation
  - PostgreSQL database with all models
  - Real-time radar with Leaflet.js
  - Automated billing system
  - RBAC with audit logging

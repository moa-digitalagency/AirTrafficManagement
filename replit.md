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
│   ├── api_client.py       # External API integrations
│   ├── flight_tracker.py   # Real-time flight tracking
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

### Core Configuration
| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes (auto-configured) |
| `SESSION_SECRET` | Flask session secret key | Yes |
| `REDIS_URL` | Redis connection for Celery | Yes (for async) |

### External Flight Data APIs
| Variable | Description | Required |
|----------|-------------|----------|
| `AVIATIONSTACK_API_KEY` | AviationStack API key (primary flight data source) | Yes* |
| `AVIATIONSTACK_API_URL` | AviationStack API URL (default: http://api.aviationstack.com/v1) | No |
| `ADSBEXCHANGE_API_KEY` | ADSBexchange API key (fallback flight data source) | No |
| `ADSBEXCHANGE_API_URL` | ADSBexchange API URL | No |

### Weather Data APIs
| Variable | Description | Required |
|----------|-------------|----------|
| `OPENWEATHERMAP_API_KEY` | OpenWeatherMap API key (weather overlay on radar) | Yes* |
| `OPENWEATHERMAP_API_URL` | OpenWeatherMap API URL (default: https://api.openweathermap.org/data/2.5) | No |
| `AVIATIONWEATHER_API_URL` | Aviation Weather API URL for METAR/TAF data | No |

### Email Configuration (Invoice Sending)
| Variable | Description | Required |
|----------|-------------|----------|
| `MAIL_SERVER` | SMTP server (default: smtp.gmail.com) | No |
| `MAIL_PORT` | SMTP port (default: 587) | No |
| `MAIL_USERNAME` | SMTP username | No |
| `MAIL_PASSWORD` | SMTP password | No |
| `MAIL_DEFAULT_SENDER` | Default sender email | No |

*Required for real-time data. System falls back to simulation if not configured.

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
- RDC airspace boundary visualization with geofencing
- Dynamic aircraft icons (size by altitude, color by status)
- Weather overlay layers (clouds, precipitation, pressure, wind)
- Advanced filters (altitude range, operator, status, in-RDC)
- Data tags showing callsign, flight level, speed
- Multi-layer control (basemap selection: dark/satellite/streets)
- Airport weather on click (METAR/current conditions)

### 2. Overflight Tracking (`/radar/overflights`)
- Automatic detection of aircraft entering RDC airspace
- Geofencing using Shapely for "Point in Polygon" calculations
- Entry/exit point recording with timestamps
- Distance and duration calculation
- Trajectory breadcrumb trail

### 3. ATM Terminal (`/radar/terminal`)
- Inbound flight queue management
- Landing cycle tracking (Approach → Touchdown → Taxi → Parking)
- Aircraft on ground monitoring
- Parking duration calculation

### 4. Billing System (`/invoices`)
- Automated invoice generation from overflights and landings
- PDF export with RVA header and minimap
- Configurable tariffs (per km, per tonne, parking, night surcharge)
- Payment status tracking
- Email notification capability

### 5. Analytics/BI (`/analytics`)
- Dynamic dashboards with charts
- Traffic statistics (daily, weekly, monthly)
- Revenue analysis by airline/route
- Export capabilities (CSV, JSON, PDF)

### 6. Administration (`/admin`)
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
- `GET /radar/api/flights` - Active flights (uses AviationStack → ADSBexchange fallback)
- `GET /radar/api/boundary` - RDC boundary GeoJSON
- `GET /radar/api/alerts` - Active alerts
- `GET /radar/api/airports` - Domestic airports
- `GET /radar/api/weather/tiles` - Weather tile layer URLs
- `GET /radar/api/weather/airport/<icao>` - Airport weather and METAR

### Flights API
- `GET /api/flights` - List flights
- `GET /api/flights/<id>` - Flight details
- `GET /api/overflights` - Overflight sessions

## External API Integration

### Flight Data (Primary: AviationStack)
The system uses AviationStack API as primary source for real-time flight positions:
- Position data: latitude, longitude, altitude, heading, speed
- Aircraft info: registration, type, operator
- Route info: departure/arrival ICAO codes

### Flight Data (Fallback: ADSBexchange)
If AviationStack fails or is not configured, the system falls back to ADSBexchange for ADS-B data.

### Weather Data (OpenWeatherMap)
Weather overlay on radar map:
- Cloud cover layer
- Precipitation layer
- Pressure and wind layers
- Current conditions for airports

### Aviation Weather (aviationweather.gov)
METAR/TAF data for airports without API key requirement.

## Celery Tasks

### Periodic Tasks (via Celery Beat)
- `fetch_flight_positions` - Every 5 seconds
- `check_airspace_entries` - Every 10 seconds
- `generate_pending_invoices` - Every hour

### On-demand Tasks
- `process_flight_data` - Process incoming flight data
- `generate_single_invoice` - Generate specific invoice
- `send_invoice_notification` - Send invoice notification

## Tarification (Configurable in Admin)

| Charge Type | Default Rate |
|-------------|--------------|
| Overflight per km | $0.85 |
| Tonnage per tonne | $2.50 |
| Landing base fee | $150.00 |
| Landing per tonne | $3.00 |
| Parking per hour | $25.00 (1st hour free) |
| Night surcharge | 25% (18:00-06:00) |
| VAT | 16% |

## Recent Changes

- **2026-02-02**: External API Integration
  - Added services/api_client.py for AviationStack, ADSBexchange, OpenWeatherMap
  - Enhanced radar module with weather overlays and advanced filters
  - Dynamic aircraft icons based on altitude and status
  - Airport weather display (METAR/current conditions)
  - Fallback mechanism: AviationStack → ADSBexchange → Simulation

- **2026-02-02**: Initial system deployment
  - Full Python/Flask backend implementation
  - PostgreSQL database with all models
  - Real-time radar with Leaflet.js
  - Automated billing system with PDF generation
  - RBAC with audit logging
  - Celery + Redis integration for async processing

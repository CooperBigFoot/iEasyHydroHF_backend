# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the iEasyHydroHF Backend - a hydrological data management system for water monitoring, forecasting, and reporting. It handles time-series data from hydrological and meteorological stations, processes telegrams, generates bulletins, and provides forecasting capabilities.

## Tech Stack

- **Framework**: Django 5.1.1 with Django Ninja for REST API
- **Database**: TimescaleDB (PostgreSQL extension for time-series data)
- **Python**: 3.11
- **Container**: Docker with docker-compose
- **Authentication**: JWT via django-ninja-jwt

## Development Commands

### Running the Application

```bash
# Start all services (Django, TimescaleDB, docs, mailhog)
docker-compose -f local.yml up

# Run Django shell
docker-compose -f local.yml run --rm django python manage.py shell

# Run Django management commands
docker-compose -f local.yml run --rm django python manage.py <command>

# Create superuser
docker-compose -f local.yml run --rm django python manage.py createsuperuser

# Make and apply migrations
docker-compose -f local.yml run --rm django python manage.py makemigrations
docker-compose -f local.yml run --rm django python manage.py migrate
```

### Testing

```bash
# Run all tests
docker-compose -f local.yml run --rm django pytest

# Run specific test file
docker-compose -f local.yml run --rm django pytest path/to/test_file.py

# Run with coverage
docker-compose -f local.yml run --rm django coverage run -m pytest
docker-compose -f local.yml run --rm django coverage html

# Run specific test
docker-compose -f local.yml run --rm django pytest path/to/test_file.py::TestClass::test_method
```

### Code Quality

```bash
# Format code (runs ruff fix and format)
./scripts/format.sh

# Type checking
docker-compose -f local.yml run --rm django mypy sapphire_backend

# Linting
docker-compose -f local.yml run --rm django ruff sapphire_backend config docs scripts
```

## Architecture

### Core Django Apps

- **metrics**: Core time-series data models using TimescaleDB hypertables
  - `HydrologicalMetric`: 6-month chunks for water level/discharge data
  - `MeteorologicalMetric`: 120-month chunks for weather data
- **stations**: Physical and virtual station management
- **organizations**: Multi-tenant organization, basin, and region hierarchy
- **telegrams**: Automated telegram parsing and data ingestion
- **bulletins**: Hydrological bulletin generation
- **estimations**: Water discharge calculations and forecasting
- **users**: User management with role-based permissions
- **quality_control**: Data validation and history tracking
- **ingestion**: Data import pipeline
- **imomo**: Legacy data migration (excluded from linting/testing)

### API Structure

All APIs are under `/api/v1/` using Django Ninja controllers:
- Authentication: JWT-based with refresh tokens
- Permissions: Role-based (super_admin, org_admin, regular_user, regime_user)
- Controllers located in `sapphire_backend/*/api/controllers.py`
- Schemas in `sapphire_backend/*/api/schemas.py`

### Database Considerations

- Uses TimescaleDB for efficient time-series data storage
- Hypertables with automatic chunking for metrics
- Continuous aggregates for performance
- Custom database views for complex queries
- Migrations may include TimescaleDB-specific SQL

### Key Patterns

1. **Time-series Data**: Always use TimescaleDB hypertables for metrics
2. **Multi-tenancy**: Filter by organization/basin/region hierarchy
3. **API Responses**: Use Django Ninja schemas for serialization
4. **Permissions**: Check user roles and organization membership
5. **Testing**: Use factory_boy factories in `sapphire_backend/*/tests/factories.py`

## Service URLs (Local Development)

- API: http://localhost:8000/api/v1/
- Admin: http://localhost:8000/sapphire-admin/
- API Docs: http://localhost:8000/api/v1/docs
- Sphinx Docs: http://localhost:9000/
- MailHog: http://localhost:8025/

## Important Notes

- The `imomo` app contains legacy migration code - avoid modifying
- TimescaleDB requires special handling in migrations
- Virtual stations calculate values from multiple physical stations
- Telegrams follow specific meteorological/hydrological formats
- Bulletins are generated based on configurable templates
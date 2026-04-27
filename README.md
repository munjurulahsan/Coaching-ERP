# Coaching Management ERP

A Django-based ERP system for managing coaching sessions, clients, coaches, and payments.

## Setup

1. Ensure Python 3.8+ is installed.
2. Create virtual environment: `python -m venv .venv`
3. Activate: `source .venv/bin/activate` (Linux/Mac) or `.venv\Scripts\activate` (Windows)
4. Install dependencies: `pip install django`
5. Run migrations: `python manage.py migrate`
6. Create superuser: `python manage.py createsuperuser`
7. Run server: `python manage.py runserver`

## Usage

- Admin panel: http://127.0.0.1:8000/admin/
- Coaches: http://127.0.0.1:8000/coaches/
- Clients: http://127.0.0.1:8000/clients/
- Sessions: http://127.0.0.1:8000/sessions/
- Payments: http://127.0.0.1:8000/payments/

## Database

The database is SQLite (db.sqlite3). To store in Google Drive, move the db.sqlite3 file to your Google Drive folder and update the DATABASES setting in settings.py to point to that path, e.g.:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/path/to/Google Drive/coaching_erp/db.sqlite3',
    }
}
```

## Features

- Manage coaches, clients, sessions, and payments.
- Admin interface for CRUD operations.
- Basic web views for listing entities.# Coaching-ERP

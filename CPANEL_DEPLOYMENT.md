# cPanel Django Deployment Guide

This project is prepared for cPanel Python App with Python 3.11.

## cPanel Python App settings

Use these values in **Setup Python App**:

```text
Python version: 3.11.12
Application root: coaching_erp_app
Application URL: mizanurrahman.site/erp
Application startup file: passenger_wsgi.py
Application Entry point: application
```

## Environment variables

Add these variables in the cPanel Python App screen:

```text
SECRET_KEY=your-long-random-secret-key
DEBUG=False
ALLOWED_HOSTS=mizanurrahman.site,www.mizanurrahman.site
CSRF_TRUSTED_ORIGINS=https://mizanurrahman.site,https://www.mizanurrahman.site
FORCE_SCRIPT_NAME=/erp
SECURE_SSL_REDIRECT=False

DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=your-email@example.com
DJANGO_SUPERUSER_PASSWORD=choose-a-strong-owner-password

STAFF_USERNAME=Munna
STAFF_PASSWORD=Munna123

SMS_ENABLED=True
SMS_API_URL=https://xlahr.pro.bd/api.php
SMS_API_KEY=your-sms-api-key
SMS_API_KEY_PARAM=key
SMS_TO_PARAM=number
SMS_MESSAGE_PARAM=msg
SMS_EXTRA_PARAMS=type=sms
SMS_METHOD=GET
SMS_TIMEOUT_SECONDS=10
```

## Upload files

Upload the project files into the application root folder:

```text
coaching_erp_app/
```

Do not upload `.venv`, `__pycache__`, `.git`, or local backup files.

## Install dependencies

After creating the Python app, cPanel usually shows a command like:

```bash
source /home/USER/virtualenv/coaching_erp_app/3.11/bin/activate
```

Run that command in Terminal, then:

```bash
cd ~/coaching_erp_app
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --no-input
python manage.py create_admin
python manage.py create_staff
```

If you do not have Terminal access, use the **Execute python script** section:

First install packages:

```text
cpanel_pip_install.py
```

Then run setup:

```text
cpanel_setup.py
```

Then click **Run Script**.

For `create_admin` and `create_staff`, add these environment variables first if you want automatic login creation:

```text
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=your-email@example.com
DJANGO_SUPERUSER_PASSWORD=choose-a-strong-password
STAFF_USERNAME=Munna
STAFF_PASSWORD=Munna123
```

## Restart app

In cPanel **Setup Python App**, click **Restart** after installing dependencies or changing files.

Then open:

```text
https://mizanurrahman.site/erp/
https://mizanurrahman.site/erp/admin/
```

## Login roles

Owner/admin login uses the Django superuser credentials. Owner can create, edit, and delete batches and can see monthly/total collection.

Staff login uses:

```text
Username: Munna
Password: Munna123
```

Staff can use the same daily operations, but cannot create/edit/delete batches and cannot see monthly/total collection.

## Change login password

After logging in, open the dashboard and click **Change Password**.

If the app is installed under `/erp`, open:

```text
https://mizanurrahman.site/erp/password-change/
```

If the app is installed at the domain root, open:

```text
https://mizanurrahman.site/password-change/
```

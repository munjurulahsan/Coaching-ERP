# Render Deployment Guide

## 1. Push the project to GitHub

Commit only the deployment files and source changes:

```bash
git add coaching_erp/settings.py build.sh render.yaml RENDER_DEPLOYMENT.md
git commit -m "Prepare Render deployment"
git push
```

Do not commit `db.sqlite3`, `__pycache__`, or local backup files.

## 2. Create the Render services

1. Go to https://dashboard.render.com.
2. Click **New +**.
3. Choose **Blueprint**.
4. Connect the GitHub repository for this project.
5. Select the branch you pushed.
6. Click **Apply**.

Render will read `render.yaml`, create:

- `coaching-erp`: the Django web service
- `coaching-erp-db`: the PostgreSQL database

Both are set to Render's `free` plan in `render.yaml`. You can upgrade later from the Render dashboard if needed.

The build command is:

```bash
./build.sh
```

The start command is:

```bash
gunicorn coaching_erp.wsgi:application
```

## 3. Wait for the first deploy

The first deploy will install packages, collect static files, and run migrations.
When the deploy finishes, open the generated `.onrender.com` URL.

## 4. Create the admin user on the free plan

Render free web services do not include Shell access. Create the admin user with environment variables instead:

1. Open the `coaching-erp` web service.
2. Go to **Environment**.
3. Add these environment variables:

```text
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=your-email@example.com
DJANGO_SUPERUSER_PASSWORD=choose-a-strong-password
```

4. Save changes.
5. Go to **Manual Deploy**.
6. Click **Deploy latest commit**.

During deploy, `build.sh` runs `python manage.py create_admin` and creates or updates the admin user.

Then visit:

```text
https://your-render-url.onrender.com/admin/
```

## 5. Optional custom domain

If you add a custom domain, add these environment variables in the web service:

```text
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

After changing env vars, redeploy the service.

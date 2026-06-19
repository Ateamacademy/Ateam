# Running webApp locally (WSL2 / Ubuntu)

This Flask app was built for an Ubuntu/Apache production server. The steps below
reproduce that environment under WSL2 so the hardcoded `/var/www/webApp/...`
paths and native PDF libraries work with minimal changes.

The repo lives on Windows at `c:\Ateam`, which is `/mnt/c/Ateam` inside WSL.

---

## 1. Install WSL2 + Ubuntu (run in Windows PowerShell, once)

```powershell
wsl --install -d Ubuntu
```

Reboot if prompted, then open the **Ubuntu** terminal for everything below.

## 2. System packages

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip \
    postgresql libpq-dev \
    libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libcairo2 libffi-dev \
    poppler-utils
```

- `libpango*/libcairo*/libgdk-pixbuf*` → required by **WeasyPrint** (PDF generation)
- `poppler-utils` → required by **pdf2image**
- `libpq-dev` → required by **psycopg2**

## 3. PostgreSQL: match the hardcoded connection string

The app connects with `postgresql://postgres:Ateam123@localhost:5432/ateam`
(`webApp/webApp/__init__.py`). Create that DB + password:

```bash
sudo service postgresql start
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'Ateam123';"
sudo -u postgres psql -c "CREATE DATABASE ateam;"
```

## 4. Put the code where the hardcoded paths expect it

~43 paths are hardcoded as `/var/www/webApp/webApp/...`. Symlink the Windows
checkout to that location so they resolve (and you can keep editing from Windows):

```bash
sudo mkdir -p /var/www
sudo ln -s /mnt/c/Ateam/webApp /var/www/webApp
```

Now `/var/www/webApp/webApp/` is the Flask package.

## 5. Create the writable folders the app uses

```bash
cd /var/www/webApp/webApp
mkdir -p files payslips userFiles marketPlaceFiles contracts \
         grade-boundaries static/CS310images templates/email_templates
```

## 6. Python virtual environment + dependencies

```bash
cd /var/www/webApp
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements-local.txt
```

> `requirements-local.txt` is the complete list (the original `requirements.txt`
> was missing ~11 packages). If `weasyprint` fails to build, re-check the
> `libpango/libcairo` packages from step 2.

## 7. Initialise the database + create an admin login

```bash
cd /var/www/webApp
PYTHONPATH=/var/www/webApp python3 bootstrap_local.py
```

This creates all tables, seeds sample data, and creates:

```
email:    admin@local
password: password
```

(`db_init()` alone does **not** create any login user or roles — this script adds
an admin role + user with all permissions so you avoid 403/503 walls.)

## 8. Run

```bash
cd /var/www/webApp
PYTHONPATH=/var/www/webApp python3 run_local.py
```

Open <http://127.0.0.1:5000/> and log in with the admin credentials above.

---

## What works vs. what won't (locally)

| Feature | Status |
|---|---|
| Login, dashboards, timetable, CRUD, file up/download | ✅ works |
| PDF generation (reports, payslips, predicted papers) | ✅ once GTK/Poppler installed (steps 2) |
| Outbound email | ⚠️ uses live IONOS creds in `EmailSender.py`; calls will try to send. Leave alone or stub out for local. |
| Automatic maths marker (`/automatic_maths_marker`) | ❌ shells out to a hardcoded `python3.8` venv + ML model; skip locally |

## Notes / gotchas
- Always run with `PYTHONPATH=/var/www/webApp` and import as the `webApp` package
  — the code uses top-level `from Schema import *` / `from functions import *`,
  so running the inner files directly fails.
- `debug=True` is on with the reloader **off** (the APScheduler in `__init__.py`
  double-starts under the reloader).
- Secrets now come from env vars (`SECRET_KEY`, `DATABASE_URL`, `MAIL_*`); see `.env.example`. Local-dev fallbacks apply if unset — set real values for any deployment.
- First-load pages may be slow from `/mnt/c`; that's WSL disk crossing, not the app.
```

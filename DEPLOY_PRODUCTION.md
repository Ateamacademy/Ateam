# Deploying to production (ateamacad.co.uk)

The live site is a Flask app served by **Apache + mod_wsgi** on an Ubuntu VPS
(`217.154.50.100`), rooted at **`/var/www/webApp/`**, importing the `webApp`
package via `webapp.wsgi`. Production has **drifted** from this repo (older
registration form, no pricing/CRM/seating), so this is a real cutover of a live
system holding real student data. **Do the backups. They are the whole safety net.**

Everything here is meant to be run **on the server** over SSH as a user with
`sudo`. Commands are copy-paste ready; the only things to fill in are the DB
connection details and the secret values.

The migration is **data-safe by construction**: it only creates missing tables
and adds new nullable columns — it never drops, alters, or overwrites existing
rows, and (unlike the local bootstrap) it never creates the `admin@local`
backdoor account or seeds demo data. This was proven against a simulated copy of
the old production schema (`it_migrate_prod.py`).

---

## 0. Before you start

```bash
ssh <you>@217.154.50.100
APP=/var/www/webApp                 # the repo root on the server
cd "$APP"

# Confirm the layout and how the DB is reached.
ls webapp.wsgi webApp/__init__.py   # both should exist
cat .env 2>/dev/null || echo "no .env yet"   # DATABASE_URL lives here (or a fallback is used)
python3 -c "import sys; print(sys.version)"
```

Note the **database connection string** the live app uses. It comes from
`DATABASE_URL` in `/var/www/webApp/.env`; if that file/line is absent the app
falls back to `postgresql://postgres:Ateam123@localhost:5432/ateam`. Everything
below assumes `$PGURL` holds that exact string:

```bash
PGURL="postgresql://USER:PASSWORD@localhost:5432/ateam"   # <-- set to the live one
```

---

## 1. Full backups (do not skip)

```bash
STAMP=$(date +%Y%m%d-%H%M%S)
mkdir -p ~/deploy-backups

# (a) database — a complete logical dump
pg_dump "$PGURL" > ~/deploy-backups/ateam-db-$STAMP.sql
ls -lh ~/deploy-backups/ateam-db-$STAMP.sql        # sanity: non-trivial size

# (b) the entire app directory, including uploaded student files
sudo tar czf ~/deploy-backups/webApp-$STAMP.tar.gz -C /var/www webApp
ls -lh ~/deploy-backups/webApp-$STAMP.tar.gz
```

Keep both files until the new deploy has been verified in production for a day.

---

## 2. Capture the live code as it is now

If `/var/www/webApp` is a git checkout, snapshot the drift as a branch so nothing
is lost; if it is not, the tar from step 1 is your snapshot.

```bash
cd "$APP"
if [ -d .git ]; then
  git stash -u 2>/dev/null || true
  git branch prod-live-$STAMP 2>/dev/null || true    # a named pointer to what was live
  git rev-parse --short HEAD
else
  echo "Not a git checkout — the tar in step 1 is the code backup."
fi
```

---

## 3. Put the new code in place

**If `/var/www/webApp` is a git checkout of `Ateamacademy/Ateam`:**

```bash
cd "$APP"
git fetch origin
git checkout main
git pull --ff-only origin main
git log --oneline -1        # expect the latest commit (GHL inbound sync / prod migration)
```

**If it is not a git checkout** (code was copied manually), OVERLAY the new code
onto the live tree with rsync. This is safer than swapping the whole directory:
it updates code files and adds new ones, but because `.env` and every uploaded
data directory (userFiles, contracts, marketplace files, generated PDFs, …) are
gitignored they are **not in the clone**, so rsync leaves them untouched. No data
is moved or deleted.

```bash
cd /tmp && rm -rf ateam-fresh
git clone --depth 1 https://github.com/Ateamacademy/Ateam.git ateam-fresh

# /var/www/webApp corresponds to the repo's OUTER webApp/ dir (so that
# /var/www/webApp/webApp is the Flask package). Overlay from there.
# --exclude .env: never overwrite the live secrets file.
# NO --delete: existing uploads/data dirs on the server are preserved.
sudo rsync -a --exclude='.env' /tmp/ateam-fresh/webApp/ /var/www/webApp/
rm -rf /tmp/ateam-fresh
cd "$APP"
ls webApp/__init__.py migrate_production.py   # package + migration script must resolve
```
> The tar from step 1 is the full rollback for this path. If you would rather
> convert the tree to a proper git checkout for future deploys, do that as a
> separate, later task — not during the cutover.

---

## 4. Python dependencies

Install into whatever interpreter/venv mod_wsgi uses (check the Apache vhost for
`WSGIDaemonProcess ... python-home=...`; if there's no venv it's the system
`python3`).

```bash
cd "$APP"
# with a venv:
#   source /path/to/venv/bin/activate
python3 -m pip install -r requirements-local.txt   # includes stripe + requests
```

---

## 5. Environment variables (`/var/www/webApp/.env`)

The app auto-loads `/var/www/webApp/.env` (python-dotenv) for both the web
process and the migration script. Create/extend it from the template:

```bash
cd "$APP"
[ -f .env ] || cp .env.example .env    # .env and .env.example both live in $APP
sudoedit .env      # or: nano .env
```

Ensure these are set (see `.env.example` for the full annotated list):

- `DATABASE_URL`, `SECRET_KEY` — required.
- `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET` — for prepayment.
- `GHL_PRIVATE_TOKEN`, `GHL_LOCATION_ID` — outbound CRM sync.
- `GHL_INBOUND_SECRET` — inbound GHL webhook (X-Webhook-Key).

Keep `.env` readable only by the app user: `chmod 600 .env`.

---

## 6. Run the one-off schema migration

```bash
cd "$APP"                                          # = /var/www/webApp
PYTHONPATH=/var/www/webApp python3 migrate_production.py
```

Expected output ends with `[migrate] OK — schema is up to date and no core rows
were lost.` and prints matching `[before]`/`[after]` row counts. If it prints
`ROW COUNT DROPPED`, **stop and roll back** (section 8) — do not reload Apache.

---

## 7. Reload Apache and verify

```bash
sudo systemctl reload apache2          # or: sudo touch /var/www/webApp/webapp.wsgi

# --- smoke tests ---
curl -sSI https://ateamacad.co.uk/ | head -1                       # 200/302
# the NEW structured registration form is live if this matches:
curl -s https://ateamacad.co.uk/register_exam_interest | grep -c examSelections   # expect >=1
```

Then in a browser:
1. Log in with a **real** existing officer account — confirm existing students,
   exams and data are all present and unchanged.
2. Open **Exam Students** — the new Exam Centre column and quote line render.
3. Submit a test registration on `/register_exam_interest` — it appears as a
   pending candidate (and, once GHL keys are set, in GoHighLevel).
4. If GHL inbound is configured, point the GHL workflow webhook at
   `https://ateamacad.co.uk/ghl_inbound` (header `X-Webhook-Key: <GHL_INBOUND_SECRET>`)
   and confirm a test contact appears on the platform.

---

## 8. Rollback (if anything looks wrong)

Set `STAMP` to the exact value from step 1 first, and confirm the backup exists
BEFORE removing anything — the guard below refuses to delete the live tree if the
backup is missing.

```bash
STAMP=20240101-000000               # <-- the real stamp from step 1
BK=~/deploy-backups/webApp-$STAMP.tar.gz

# --- code rollback ---
# git checkout used?  ->  cd /var/www/webApp && git checkout prod-live-$STAMP
# rsync/manual path   ->  restore the whole tree from the tar (guarded):
if [ -f "$BK" ]; then
  sudo rm -rf /var/www/webApp
  sudo tar xzf "$BK" -C /var/www          # recreates /var/www/webApp exactly as backed up
else
  echo "ABORT: backup $BK not found — do NOT delete the live tree."
fi

# --- database rollback (only if the DATA itself looks wrong) ---
# The migration is purely additive (new nullable columns + new tables), so a
# code-only rollback usually needs NO DB restore — the old code just ignores the
# extra schema. Restore the DB only if rows are actually wrong:
#   psql "$PGURL" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
#   psql "$PGURL" < ~/deploy-backups/ateam-db-$STAMP.sql

sudo systemctl reload apache2
```

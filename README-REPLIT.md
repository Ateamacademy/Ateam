# Running the A-Team webApp on Replit

This repo is pre-configured for Replit (`.replit`, `replit.nix`,
`run_replit.py`, root `requirements.txt`).

## Import

1. On Replit choose **Create Repl → Import from GitHub** and pick
   `Ateamacademy/Ateam` (re-import or pull to update an existing Repl).
2. Replit reads `.replit` automatically; the Python + PostgreSQL modules are
   declared there.

## One-time setup

1. **Database** — open the *PostgreSQL* tool in the Repl and create the
   database. Replit injects `DATABASE_URL` into the environment, which the app
   reads directly.
2. **Secrets** (Tools → Secrets):
   - `SECRET_KEY` — generate one with
     `python -c "import secrets; print(secrets.token_hex(32))"`.
     If unset, the app now uses a random per-process key (sessions reset on
     every restart, but they are not forgeable).
   - `MAIL_NOREPLY_PASSWORD`, `MAIL_EXAMS_PASSWORD` — only if outbound email
     (IONOS SMTP) is needed; leave unset to disable sending.
3. **Bootstrap the DB** (Shell tab):

   ```bash
   python3 webApp/bootstrap_local.py
   ```

   This creates all tables plus an admin login: `admin@local` / `AdminLocal1`.
   Change that password immediately if the Repl is public.

4. Press **Run**. The app serves on port 5000, exposed by Replit on port 80.

## Known limitations on Replit

- Several ops features use hardcoded `/var/www/webApp/...` paths from the
  original Apache server (payslips, contracts, the CS310 maths-marking
  pipeline, mass-print reports). Those directories don't exist on Replit, so
  the related pages will error; the core system (logins, timetable, students,
  lessons, exams, grades) works.
- Uploaded files (`files/`, `userFiles/`) are stored on the Repl's disk and
  are not committed to git.
- The Laravel marketing site in `webApp2/` is not run by this config; it
  would need its own PHP environment.

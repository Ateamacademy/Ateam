# Deploying the A-Team app on Render

Render runs this Flask + PostgreSQL app on a real URL and **auto-deploys on
every push to `main`** — so once it's set up, any change lands live in ~2 min
with nothing for you to do.

## One-time setup (~10 minutes)

1. Go to **https://render.com** and sign up / log in (you can sign in with
   GitHub — easiest).
2. Click **New +** (top right) → **Blueprint**.
3. **Connect the `Ateamacademy/Ateam` repo.** If Render asks for GitHub
   permission, grant it access to that repo.
4. Render reads `render.yaml` automatically and shows a plan:
   - **ateam-db** — a free PostgreSQL database
   - **ateam-academy** — the web service
   Click **Apply** / **Create**.
5. Wait for the first build. It installs the Python dependencies (a few minutes),
   then starts the app. The first boot creates the database tables and an admin
   login automatically.
6. When the service shows **Live**, click its URL (looks like
   `https://ateam-academy.onrender.com`). You'll see the **reskinned login page**.

## Logging in

- **Email:** `admin@local`
- **Password:** `AdminLocal1`

(This admin is created on first boot with full permissions so you can explore
every page. Change the password once you're in for anything real.)

## Good to know

- **Auto-deploy:** every time the code is pushed to `main`, Render rebuilds and
  redeploys on its own. Just refresh the URL to see updates.
- **Free tier sleeps:** after ~15 min idle the free service spins down, so the
  first visit afterwards takes ~30 seconds to wake. Upgrading the service (a few
  £/month) keeps it always-on.
- **Free database expires:** Render's free PostgreSQL is deleted after 90 days
  unless upgraded — fine for evaluating, worth upgrading if this becomes the
  real thing.
- **Known limits (styling is unaffected):** a few legacy features that read/write
  hardcoded server paths (`/var/www/...`) — some file uploads and PDF exports —
  won't fully work on a hosted box until those paths are modernised. Browsing,
  logging in and viewing every page all work. Tell me if you want those file
  features made hosting-safe and I'll do it.

## If a deploy ever fails

Open the service in Render → **Logs** tab, and send me the last ~20 lines. The
app is built to keep booting even if optional PDF/chart libraries are missing,
so most issues will be quick to fix.

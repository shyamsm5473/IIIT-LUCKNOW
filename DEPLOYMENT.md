# Neon PostgreSQL & Render Deployment Instructions

Because Render uses an ephemeral filesystem on its free tier, any local SQLite databases will be wiped on every deployment. This will cause data loss and missing tables (e.g. `no such table: related_publication_publication`).

To fix this permanently, we have migrated to **Neon** (a free, non-expiring hosted PostgreSQL). We use Neon instead of Render's free PostgreSQL because Render's free Postgres auto-deletes after 30 days.

### Manual Setup Steps (Already Completed)
The following steps have already been done to resolve the database persistence issue:

1. **Created a Free Neon Postgres Project:**
   - A Neon project was created to host the database.
   - The connection string (which includes `?sslmode=require` for secure SSL connections) was copied from the Neon dashboard.

2. **Configured Environment Variables on Render:**
   - Navigated to the Web Service in the Render dashboard.
   - Under the **Environment** tab, added the `DATABASE_URL` key.
   - Pasted the Neon connection string as the value. *(Note: `django-environ` safely handles parsing this URL and the `sslmode=require` query parameter automatically.)*

3. **Configured Migrations on Deploy:**
   - Under the **Settings** tab in the Render Web Service, the **Pre-Deploy Command** (or Start Command) was set to include:
     ```bash
     python manage.py migrate
     ```
   - This ensures all tables are rebuilt and verified before the app boots up on every deploy.

### Known Limitations
> [!NOTE]
> Neon's free tier automatically pauses compute resources after a period of inactivity to save costs. If the site receives no traffic for a while, the very first request that hits the database will trigger a "cold start." This means the database may take 2–5 seconds to wake up, causing a slight delay on that first page load. This is a known limitation of the free tier and not a bug in the code.

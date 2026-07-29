# Render Deployment Instructions

Because Render uses an ephemeral filesystem, any local SQLite databases will be wiped on every deployment. This will cause data loss and missing tables (e.g. `no such table: related_publication_publication`).

To fix this, you must migrate to a permanent PostgreSQL database. 

### Step 1: Create a PostgreSQL Instance
1. Go to your [Render Dashboard](https://dashboard.render.com).
2. Click **New +** and select **PostgreSQL**.
3. Create the database (the Free tier is fine).
4. Once created, copy the **Internal Database URL** (starts with `postgres://...`).

### Step 2: Configure Environment Variables
1. Navigate back to your Web Service (e.g., `iiit-lucknow`) in the Render dashboard.
2. Go to the **Environment** tab.
3. Add a new variable:
   - **Key**: `DATABASE_URL`
   - **Value**: *(Paste the Internal Database URL from Step 1)*

### Step 3: Run Migrations on Deploy
Since we need to ensure database tables are created automatically before the app runs, you need to update the startup or pre-deploy sequence.
1. Go to the **Settings** tab of your Web Service.
2. Set your **Pre-Deploy Command** (or prepend it to your Start Command) to:
   ```bash
   python manage.py migrate
   ```
   *(If you are modifying the Start Command directly, it should look like: `python manage.py migrate && gunicorn iiitl_project.wsgi:application`)*

Once these steps are completed, your database will persist across deployments and all "no such table" errors will be resolved.

# 1-Click Free Cloud Deployment Guide: Render & Railway

This guide shows you how to deploy **CivicPulse AI • CleanCity Copilot** with 1 click on **Render** or **Railway** with free managed HTTPS, zero Linux server management, and automated deployments from GitHub.

---

## Step 1: Push Code to GitHub

All files have already been committed to your local `main` branch.

1. Go to [github.com/new](https://github.com/new) and create a repository named: `civicpulse-ai` (Public or Private).
2. In your local terminal, link and push the repository:

```bash
git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/civicpulse-ai.git
git branch -M main
git push -u origin main
```

---

## Option A: Deploy on Render (Recommended Blueprint)

Render automatically reads the bundled [`render.yaml`](../render.yaml) and provisions both the FastAPI portal and Streamlit dashboard together.

1. Go to [dashboard.render.com](https://dashboard.render.com/) (Sign in with your GitHub account).
2. Click the blue **New +** button in the top right, then select **Blueprint**.
3. Select your `civicpulse-ai` repository.
4. Render will detect `render.yaml` and display the blueprint configuration:
   - **Service 1 (`civicpulse-portal`)**: FastAPI backend + responsive web portal + SQLite database.
   - **Service 2 (`civicpulse-streamlit`)**: Streamlit municipal dashboard connected to the portal.
5. Click **Apply**.
6. Render builds the services in parallel and provides two live HTTPS URLs:
   - Portal & API: `https://civicpulse-portal.onrender.com`
   - Streamlit Admin: `https://civicpulse-streamlit.onrender.com`

---

## Option B: Deploy on Railway (Ultra Fast)

Railway automatically detects [`railway.json`](../railway.json) and [`Procfile`](../Procfile).

1. Go to [railway.app](https://railway.app/) and sign in with GitHub.
2. Click **+ New Project** -> **Deploy from GitHub repo**.
3. Select `civicpulse-ai`.
4. Railway builds and boots the application within 60 seconds.
5. In your project dashboard, click **Settings** -> **Networking** -> **Generate Domain**.
6. Your live public portal is instantly accessible at `https://civicpulse-production.up.railway.app`!

---

## Automated Verification

Once deployed, visit your live URL:
- `https://<YOUR_APP_URL>/` - Municipal portal, citizen reporting form, live heatmap, and status tracker.
- `https://<YOUR_APP_URL>/api/health` - Backend health verification.
- `https://<YOUR_APP_URL>/docs` - Interactive OpenAPI documentation.

# U-Loader — Universal Media Downloader

A high-performance universal media downloader built with **React (Vite + TailwindCSS)** for the frontend and **Django + Celery + Redis + Docker** for the backend.

Supports downloading from:
- 🔴 **YouTube**: Videos up to 4K (with audio remuxing) and 320kbps / 192kbps MP3 extraction
- 🟣 **Instagram**: Reels, videos, and carousels
- 🔷 **TikTok**: Clean HD videos without any watermark
- 🔴 **Pinterest**: Video pins in high quality
- 🟢 **Spotify**: Tracks, Albums, and complete Playlists with embedded ID3 metadata, album art, and multi-track ZIP archive export

---

## 🏗️ System Architecture

- **Frontend (`loader.claive.uz`)**: Hosted as a static Single Page Application on **Cloudflare Pages**.
- **Backend API (`api-loader.claive.uz`)**: Deployed on your **VPS** via Docker Compose behind **NGINX Proxy Manager (NPM)**.
- **Asynchronous Task Queue**: Celery workers handle heavy media extraction, FFmpeg transcoding, and Spotify playlist zipping to avoid Cloudflare's 100-second request timeout limit.
- **Auto-Cleanup**: Celery Beat runs every 15 minutes, automatically removing generated files older than 60 minutes to ensure your VPS storage remains clean.

---

## 🚀 Deployment Guide

### Part 1: Backend Deployment on VPS (`api-loader.claive.uz`)

#### 1. Clone & Configure
On your VPS terminal:
```bash
git clone <your-repo-url> /opt/u-loader
cd /opt/u-loader

# Copy environment template
cp .env.example .env
```

Edit `.env`:
```ini
DEBUG=0
SECRET_KEY=generate-a-strong-random-key
ALLOWED_HOSTS=api-loader.claive.uz,localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=https://loader.claive.uz

# Port mapped on VPS for NGINX Proxy Manager
API_HOST_PORT=8088

# PostgreSQL & Celery
POSTGRES_DB=uloader_db
POSTGRES_USER=uloader_user
POSTGRES_PASSWORD=your_strong_password
```

#### 2. Launch Docker Containers
```bash
docker compose up -d --build
```
This boots up:
- `u_loader_api`: Django REST API with Gunicorn (port 8088)
- `u_loader_worker`: Celery worker with `ffmpeg` and `yt-dlp`
- `u_loader_beat`: Celery Beat periodic scheduler (auto file cleanup)
- `u_loader_redis`: Redis broker & cache
- `u_loader_postgres`: PostgreSQL database

#### 3. Configure NGINX Proxy Manager (NPM)
Open your NPM admin dashboard:
1. Go to **Proxy Hosts** $\rightarrow$ **Add Proxy Host**.
2. **Details Tab**:
   - **Domain Names**: `api-loader.claive.uz`
   - **Scheme**: `http`
   - **Forward Hostname / IP**: `172.17.0.1` (Docker default gateway) or your VPS local IP (e.g., `10.0.0.x` or public IP).
   - **Forward Port**: `8088` (or the `API_HOST_PORT` you set in `.env`)
   - Check **Block Common Exploits** and **Websockets Support**.
3. **SSL Tab**:
   - Select **Request a new SSL Certificate** (Let's Encrypt).
   - Check **Force SSL**, **HTTP/2 Support**, and agree to Terms of Service.
4. **Advanced Tab** (Recommended for large file streaming):
   ```nginx
   client_max_body_size 100M;
   proxy_read_timeout 300;
   proxy_connect_timeout 300;
   proxy_send_timeout 300;
   ```
5. Click **Save**. Verify by visiting: `https://api-loader.claive.uz/api/health/`.

---

### Part 2: Frontend Deployment on Cloudflare Pages (`loader.claive.uz`)

#### Option A: Deploy with Wrangler CLI (Fastest)
From your local terminal in `/frontend`:
```bash
cd frontend

# Login to your Cloudflare account (first time only)
npx wrangler login

# Build & deploy directly to Cloudflare Pages
npm run deploy
```
This deploys `./dist` to Cloudflare Pages project `u-loader` using `wrangler.toml`. Then attach `loader.claive.uz` in your Cloudflare Pages dashboard under **Custom Domains**.

#### Option B: Deploy via Cloudflare Git Integration
1. Go to **Cloudflare Dashboard** $\rightarrow$ **Workers & Pages** $\rightarrow$ **Create Application** $\rightarrow$ **Pages** $\rightarrow$ **Connect to Git**.
2. Select your repository.
3. Configure build settings:
   - **Project Name**: `u-loader`
   - **Framework preset**: `Vite`
   - **Root directory**: `frontend`
   - **Build command**: `npm run build`
   - **Build output directory**: `dist`
4. In **Environment Variables**, add:
   - Variable name: `VITE_API_BASE_URL`
   - Value: `https://api-loader.claive.uz`
5. Click **Save and Deploy**.
6. Once deployed, go to **Custom Domains** tab and add `loader.claive.uz`.

---

## 🍪 Optional: Instagram / YouTube Cookies

If Instagram challenges your datacenter VPS IP for certain Reels:
1. Export your browser cookies in Netscape format using an extension like *Get cookies.txt LOCALLY*.
2. Place the file on your VPS at `/opt/u-loader/backend/cookies/instagram.txt` (or `cookies.txt`).
3. The Docker container automatically mounts this folder into `/app/cookies`.

---

## 💻 Local Development

### Backend
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

# Run migrations
python backend/manage.py migrate

# Run dev server
python backend/manage.py runserver 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## 🧪 Testing

Run backend tests:
```bash
python backend/manage.py test downloader
```
Build frontend production bundle:
```bash
cd frontend && npm run build
```

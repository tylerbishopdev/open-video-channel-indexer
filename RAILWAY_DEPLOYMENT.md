# Railway Deployment Guide

## Overview
This app consists of:
- **Web Service**: Flask API + frontend search interface
- **Cron Service**: Periodic indexer to populate the database
- **Database**: SQLite with persistent volume

## Step-by-Step Deployment

### 1. Create New Railway Project

Visit: https://railway.app/new

1. Click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Choose **`tylerbishopdev/open-video-channel-indexer`**
4. Name it: **"Open Video Indexer"**

### 2. Configure Main Web Service

After the project is created:

1. **Service Settings**:
   - Service Name: `web`
   - Root Directory: `/`
   - Build Command: (auto-detected from Dockerfile)
   - Start Command: (configured in railway.toml)

2. **Add Persistent Volume**:
   - Go to **Variables** tab
   - Click **"New Variable"** → **"Add Volume"**
   - Mount Path: `/app/data`
   - This ensures your SQLite database persists across deployments

3. **Environment Variables**:
   Add these in the **Variables** tab:
   ```
   DB_PATH=/app/data/open_video_channels.db
   PORT=${{PORT}}
   ```

4. **Generate Domain**:
   - Go to **Settings** → **Networking**
   - Click **"Generate Domain"**
   - Your app will be available at: `https://your-app.railway.app`

### 3. Add Cron Service (Indexer)

1. In your Railway project, click **"+ New"** → **"Service"**
2. Select **"GitHub Repo"** → Same repo
3. **Configure Cron Service**:
   - Service Name: `indexer-cron`
   - Dockerfile Path: `cron.Dockerfile`
   - Start Command:
     ```bash
     sh -c 'while true; do python scripts/indexer.py index; sleep 86400; done'
     ```
   - This runs the indexer once per day (86400 seconds)

4. **Share the Volume**:
   - In the cron service, go to **Variables** tab
   - Add the same volume from the web service
   - Mount Path: `/app/data`
   - This ensures both services access the same database

5. **Environment Variables**:
   ```
   DB_PATH=/app/data/open_video_channels.db
   ```

### 4. Initial Database Population

After deployment, trigger the first index manually:

**Option A: Via Railway CLI**
```bash
railway run --service indexer-cron python scripts/indexer.py index
```

**Option B: Via Railway Dashboard**
1. Go to the `indexer-cron` service
2. Click **"Deployments"** tab
3. Click on the active deployment
4. Open the **"Terminal"** or **"Logs"**
5. The indexer should start automatically

### 5. Verify Deployment

Check your web service:
```bash
curl https://your-app.railway.app/health
```

Should return:
```json
{
  "status": "healthy",
  "database": "/app/data/open_video_channels.db"
}
```

Check stats (after indexing completes):
```bash
curl https://your-app.railway.app/api/stats
```

### 6. Configure Cron Schedule (Optional)

To change the indexing frequency, update the cron service start command:

- **Every 12 hours**: `sleep 43200`
- **Every 6 hours**: `sleep 21600`
- **Every hour**: `sleep 3600`

## Architecture Diagram

```
┌─────────────────────────────────────┐
│     Railway Project                 │
│                                     │
│  ┌─────────────┐   ┌─────────────┐│
│  │ Web Service │   │ Cron Service││
│  │   (Flask)   │   │  (Indexer)  ││
│  └──────┬──────┘   └──────┬──────┘│
│         │                 │        │
│         └────────┬────────┘        │
│                  ▼                 │
│         ┌────────────────┐         │
│         │ Persistent     │         │
│         │ Volume         │         │
│         │ (SQLite DB)    │         │
│         └────────────────┘         │
└─────────────────────────────────────┘
```

## Troubleshooting

### Web service won't start
- Check logs in Railway dashboard
- Verify PORT environment variable is set
- Ensure volume is mounted at `/app/data`

### Database is empty
- Check cron service logs
- Manually trigger indexer:
  ```bash
  railway run --service indexer-cron python scripts/indexer.py index 10
  ```
- Verify DB_PATH environment variable

### Services can't share database
- Both services must mount the same volume
- Verify mount paths are identical: `/app/data`
- Check environment variables match

## Cost Estimate

- **Web Service**: ~$5/month (minimal traffic)
- **Cron Service**: ~$2/month (runs once daily)
- **Volume (1GB)**: Free tier included
- **Total**: ~$7/month or less with Railway's free tier

## Monitoring

### View Logs
```bash
# Web service
railway logs --service web

# Cron service
railway logs --service indexer-cron
```

### Check Database Size
In Railway dashboard → Volume metrics

### Monitor Health
Set up Railway's built-in health checks:
- Health Check Path: `/health`
- Timeout: 100s

## Backup Strategy

### Manual Backup
```bash
# Export database to JSON
railway run --service web python scripts/indexer.py export

# Download from Railway
railway volume download data/channels_index.json
```

### Automated Backups
Consider adding a third service for automated backups to S3 or similar.

## Updating the App

1. Push changes to GitHub
2. Railway auto-deploys on push to main branch
3. Zero-downtime deployment
4. Database persists through deployments

## Environment-Specific Configuration

### Production
```env
DB_PATH=/app/data/open_video_channels.db
PORT=${{PORT}}
```

### Staging (Optional)
Create a separate Railway environment:
- Different volume for staging DB
- Reduced cron frequency for testing

## Security

- SQLite database is not exposed publicly
- Only accessible to services within Railway project
- No authentication needed (internal only)
- Frontend is public (read-only access)

## Performance Optimization

- **Web Service**: Increase workers in railway.toml if needed
  ```toml
  startCommand = "gunicorn --workers 8 --bind 0.0.0.0:$PORT scripts.app:app"
  ```

- **Database**: SQLite FTS is fast for read-heavy workloads
- **Caching**: Add Redis if search performance degrades

## Next Steps

1. Add custom domain (optional)
2. Set up monitoring/alerts
3. Configure backup strategy
4. Add rate limiting for API
5. Implement analytics

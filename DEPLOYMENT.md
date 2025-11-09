# Deployment Guide for Open.Video Channel Indexer

This guide will walk you through deploying the Open.Video Channel Indexer to Vercel with Postgres database.

## Prerequisites

- A [Vercel](https://vercel.com) account
- A [GitHub](https://github.com) account (recommended for automatic deployments)
- Node.js 18+ installed locally (for local development)

## Step 1: Push to GitHub

1. Create a new repository on GitHub
2. Push your code:

```bash
git init
git add .
git commit -m "Initial commit: Next.js migration"
git remote add origin https://github.com/YOUR_USERNAME/open-video-channel-indexer.git
git push -u origin main
```

## Step 2: Deploy to Vercel

### Option A: Via Vercel Dashboard (Recommended)

1. Go to [vercel.com](https://vercel.com) and sign in
2. Click "Add New" → "Project"
3. Import your GitHub repository
4. Vercel will auto-detect Next.js settings
5. Click "Deploy"

### Option B: Via Vercel CLI

```bash
npm install -g vercel
vercel login
vercel
```

Follow the prompts to deploy.

## Step 3: Set Up Vercel Postgres

1. In your Vercel project dashboard, go to the "Storage" tab
2. Click "Create Database"
3. Select "Postgres"
4. Choose a database name (e.g., `open-video-db`)
5. Select a region close to your users
6. Click "Create"

Vercel will automatically add these environment variables to your project:
- `POSTGRES_URL`
- `POSTGRES_PRISMA_URL`
- `POSTGRES_URL_NON_POOLING`
- `POSTGRES_USER`
- `POSTGRES_HOST`
- `POSTGRES_PASSWORD`
- `POSTGRES_DATABASE`

## Step 4: Configure Environment Variables

1. In your Vercel project, go to "Settings" → "Environment Variables"
2. Add a new variable:
   - Key: `CRON_SECRET`
   - Value: Generate a random secret (e.g., using `openssl rand -base64 32`)
   - Environment: Production, Preview, Development

## Step 5: Initialize the Database

After deployment, initialize your database schema:

```bash
curl -X POST https://your-app.vercel.app/api/init-db \
  -H "Authorization: Bearer YOUR_CRON_SECRET"
```

Replace `YOUR_CRON_SECRET` with the value you set in Step 4.

## Step 6: Verify Cron Job

Vercel Cron jobs are configured in `vercel.json`. The indexer runs every 6 hours:

```json
{
  "crons": [
    {
      "path": "/api/cron/index?max=100",
      "schedule": "0 */6 * * *"
    }
  ]
}
```

You can view cron logs in the Vercel dashboard under "Deployments" → Select deployment → "Functions" tab.

## Step 7: Manual Indexing (Optional)

To manually trigger indexing:

```bash
curl "https://your-app.vercel.app/api/cron/index?max=50" \
  -H "Authorization: Bearer YOUR_CRON_SECRET"
```

Parameters:
- `max`: Number of channels to index (default: 100)
- `rate`: Milliseconds between requests (default: 500)

## Local Development

1. Install dependencies:
```bash
npm install
```

2. Create a `.env.local` file:
```env
# Get these from Vercel dashboard → Storage → Postgres → .env.local tab
POSTGRES_URL="..."
POSTGRES_PRISMA_URL="..."
POSTGRES_URL_NON_POOLING="..."
POSTGRES_USER="..."
POSTGRES_HOST="..."
POSTGRES_PASSWORD="..."
POSTGRES_DATABASE="..."

CRON_SECRET="your-local-secret"
```

3. Initialize the database:
```bash
npm run dev
# In another terminal:
curl -X POST http://localhost:3000/api/init-db \
  -H "Authorization: Bearer your-local-secret"
```

4. Test locally:
```bash
npm run dev
```

Visit `http://localhost:3000`

## Customizing the Cron Schedule

Edit `vercel.json` to change the indexing frequency:

- Every hour: `"0 * * * *"`
- Every 12 hours: `"0 */12 * * *"`
- Daily at 3am: `"0 3 * * *"`
- Twice daily (3am, 3pm): `"0 3,15 * * *"`

See [crontab.guru](https://crontab.guru/) for more schedule patterns.

## Monitoring & Logs

1. **Function Logs**: Vercel Dashboard → Deployments → Select deployment → Functions tab
2. **Real-time Logs**: Use Vercel CLI:
   ```bash
   vercel logs --follow
   ```

## Troubleshooting

### Database Connection Issues

If you see database connection errors:

1. Verify environment variables are set in Vercel
2. Check that Postgres database is created
3. Ensure you're using `POSTGRES_PRISMA_URL` for connection pooling

### Cron Job Not Running

1. Verify `vercel.json` is in the project root
2. Check that cron job is listed in Vercel Dashboard → Settings → Cron Jobs
3. Ensure `CRON_SECRET` environment variable is set
4. Check function logs for errors

### Search Not Working

1. Verify database is initialized (run `/api/init-db`)
2. Check that channels are indexed (run `/api/cron/index` manually)
3. Verify `/api/stats` returns data

## Production Considerations

### Rate Limiting

The indexer includes a 500ms delay between requests by default. Adjust if needed:

```bash
curl "https://your-app.vercel.app/api/cron/index?max=100&rate=1000" \
  -H "Authorization: Bearer YOUR_CRON_SECRET"
```

### Vercel Function Limits

- **Hobby Plan**: 10-second timeout, 1024 MB memory
- **Pro Plan**: 60-second timeout, 3008 MB memory
- **Enterprise**: Custom limits

For large indexing jobs, consider:
- Reducing `max` parameter (e.g., 50 channels per cron run)
- Increasing cron frequency
- Upgrading to Pro/Enterprise plan

### Database Size

Estimate: ~500KB per 100 channels

- 1,000 channels ≈ 5 MB
- 10,000 channels ≈ 50 MB
- 100,000 channels ≈ 500 MB

Vercel Postgres limits:
- **Hobby**: 256 MB
- **Pro**: 512 GB

## Cost Estimates

### Vercel Hobby (Free)
- Free for small projects
- 100 GB bandwidth/month
- 100 hours serverless function execution

### Vercel Pro ($20/month)
- 1 TB bandwidth
- 1000 hours serverless function execution
- Postgres database included

For commercial use, consider Vercel Pro or Enterprise plans.

## Support

For issues or questions:
- [Vercel Documentation](https://vercel.com/docs)
- [Next.js Documentation](https://nextjs.org/docs)
- [GitHub Issues](https://github.com/YOUR_USERNAME/open-video-channel-indexer/issues)

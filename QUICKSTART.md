# Quick Start Guide

This guide will help you get the Open.Video Channel Indexer running locally in under 5 minutes.

## Prerequisites

- Node.js 18+ installed
- A Vercel account (free tier works)

## Step 1: Clone and Install

```bash
cd /path/to/open-video-channel-indexer
npm install
```

## Step 2: Set Up Vercel Postgres (One-Time)

1. Install Vercel CLI:
```bash
npm install -g vercel
```

2. Login to Vercel:
```bash
vercel login
```

3. Link your project:
```bash
vercel link
```

4. Create a Postgres database:
- Go to https://vercel.com/dashboard
- Select your project
- Click "Storage" tab
- Click "Create Database" → "Postgres"
- Name it `open-video-db`
- Click "Create"

5. Pull environment variables:
```bash
vercel env pull .env.local
```

This will automatically download all Postgres credentials to `.env.local`.

6. Add CRON_SECRET to `.env.local`:
```bash
echo 'CRON_SECRET="dev-secret-key"' >> .env.local
```

## Step 3: Initialize Database

```bash
# Start the dev server
npm run dev
```

In a new terminal:
```bash
# Initialize the database schema
curl -X POST http://localhost:3000/api/init-db \
  -H "Authorization: Bearer dev-secret-key"
```

You should see:
```json
{"success":true,"message":"Database initialized successfully"}
```

## Step 4: Index Some Channels (Optional)

Index the first 10 channels for testing:

```bash
curl "http://localhost:3000/api/cron/index?max=10" \
  -H "Authorization: Bearer dev-secret-key"
```

This will take about 5-10 seconds. You'll see a response like:
```json
{
  "success": true,
  "indexed": 10,
  "skipped": 0,
  "errors": 0,
  "total_processed": 10
}
```

## Step 5: Test the Search Interface

1. Open http://localhost:3000 in your browser
2. Try searching for channels
3. Check the statistics dashboard

## Step 6: Deploy to Vercel (Optional)

When you're ready to deploy:

```bash
vercel --prod
```

Or push to GitHub and connect it to Vercel for automatic deployments.

## Common Commands

### Index more channels
```bash
# Index first 50 channels
curl "http://localhost:3000/api/cron/index?max=50" \
  -H "Authorization: Bearer dev-secret-key"

# Index first 100 channels
curl "http://localhost:3000/api/cron/index?max=100" \
  -H "Authorization: Bearer dev-secret-key"
```

### Check statistics
```bash
curl http://localhost:3000/api/stats
```

### Search via API
```bash
curl "http://localhost:3000/api/search?q=cooking&limit=5"
```

### Get autocomplete suggestions
```bash
curl "http://localhost:3000/api/autocomplete?q=tech"
```

## Troubleshooting

### "Database connection failed"

Make sure you've run `vercel env pull .env.local` and that `.env.local` contains all the POSTGRES_* variables.

### "Unauthorized" error

Make sure the `Authorization` header matches your `CRON_SECRET` in `.env.local`.

### Port 3000 already in use

Kill the process using port 3000:
```bash
# macOS/Linux
lsof -ti:3000 | xargs kill -9

# Windows
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

Or use a different port:
```bash
PORT=3001 npm run dev
```

### No channels found when searching

Run the indexer first:
```bash
curl "http://localhost:3000/api/cron/index?max=20" \
  -H "Authorization: Bearer dev-secret-key"
```

## Next Steps

- Read [DEPLOYMENT.md](./DEPLOYMENT.md) for production deployment
- Customize the cron schedule in `vercel.json`
- Adjust the indexing rate limit if needed
- Add more channels by increasing the `max` parameter

## Support

For issues or questions, check:
- [Next.js Documentation](https://nextjs.org/docs)
- [Vercel Documentation](https://vercel.com/docs)
- [GitHub Issues](https://github.com/YOUR_USERNAME/open-video-channel-indexer/issues)

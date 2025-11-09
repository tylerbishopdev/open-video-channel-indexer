# Open.Video Channel Indexer

A Next.js application for creating a searchable database of all channels on open.video, deployable on Vercel.

## Features

- 🔍 **Full-text search** across channel names, handles, and descriptions
- 📊 **Live statistics** on channels and video counts
- 💾 **Vercel Postgres database** with full-text search capabilities
- 🤖 **Automated indexing** via Vercel Cron jobs
- ⚡️ **Next.js 15** with React 19 and TypeScript
- 🎨 **Modern UI** with autocomplete and responsive design
- 🚀 **One-click deployment** to Vercel

## Tech Stack

- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript
- **Database**: Vercel Postgres (PostgreSQL)
- **Deployment**: Vercel
- **Automation**: Vercel Cron Jobs
- **Styling**: CSS Modules

## Project Structure

```
open-video-channel-indexer/
├── app/
│   ├── api/
│   │   ├── search/         # Search API endpoint
│   │   ├── autocomplete/   # Autocomplete suggestions
│   │   ├── stats/          # Database statistics
│   │   ├── init-db/        # Database initialization
│   │   └── cron/
│   │       └── index/      # Automated indexing cron job
│   ├── page.tsx            # Main search interface
│   ├── layout.tsx          # Root layout
│   └── globals.css         # Global styles
├── lib/
│   ├── db.ts               # Database utilities
│   └── scraper.ts          # Channel scraping logic
├── public/                 # Static assets
├── vercel.json             # Vercel configuration & cron jobs
└── DEPLOYMENT.md           # Detailed deployment guide
```

## Quick Start

### Local Development

1. **Install dependencies:**
```bash
npm install
```

2. **Set up environment variables:**

Create a `.env.local` file with your Vercel Postgres credentials:
```env
POSTGRES_URL="your-postgres-url"
POSTGRES_PRISMA_URL="your-prisma-url"
POSTGRES_URL_NON_POOLING="your-non-pooling-url"
POSTGRES_USER="your-user"
POSTGRES_HOST="your-host"
POSTGRES_PASSWORD="your-password"
POSTGRES_DATABASE="your-database"
CRON_SECRET="your-secret-key"
```

3. **Initialize the database:**
```bash
npm run dev
# In another terminal:
curl -X POST http://localhost:3000/api/init-db \
  -H "Authorization: Bearer your-secret-key"
```

4. **Start development server:**
```bash
npm run dev
```

Visit `http://localhost:3000`

### Deploy to Vercel

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new)

See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed deployment instructions.

## API Endpoints

### Search Channels
```bash
GET /api/search?q=cooking&limit=20
```

### Autocomplete
```bash
GET /api/autocomplete?q=tech&limit=10
```

### Statistics
```bash
GET /api/stats
```

### Initialize Database
```bash
POST /api/init-db
Header: Authorization: Bearer YOUR_CRON_SECRET
```

### Manual Indexing
```bash
GET /api/cron/index?max=100&rate=500
Header: Authorization: Bearer YOUR_CRON_SECRET
```

Parameters:
- `max`: Number of channels to index (default: 100)
- `rate`: Milliseconds between requests (default: 500)

## Database Schema

### Table: `channels`

| Column          | Type      | Description                    |
|-----------------|-----------|--------------------------------|
| id              | SERIAL    | Primary key                    |
| channel_handle  | TEXT      | Channel handle (unique)        |
| channel_url     | TEXT      | Full channel URL               |
| channel_name    | TEXT      | Display name                   |
| video_count     | INTEGER   | Number of videos               |
| join_date       | TEXT      | Channel creation date          |
| last_modified   | TEXT      | Last sitemap update            |
| logo_url        | TEXT      | Profile image URL              |
| description     | TEXT      | Channel description            |
| scraped_at      | TIMESTAMP | When data was indexed          |
| search_vector   | tsvector  | Full-text search vector        |

### Indexes

- `channels_search_idx`: GIN index on `search_vector` for full-text search
- `channels_video_count_idx`: B-tree index on `video_count` for sorting

## Automated Indexing

The application uses Vercel Cron Jobs to automatically index new channels:

- **Schedule**: Every 6 hours (configurable in `vercel.json`)
- **Batch Size**: 100 channels per run (adjustable)
- **Rate Limiting**: 500ms between requests (configurable)

## Performance

- **Search**: PostgreSQL full-text search with ranking
- **Indexing Speed**: ~2 requests/second (500ms rate limit)
- **Database Size**: ~500KB per 100 channels
- **Response Time**: <100ms for search queries

## Environment Variables

Required environment variables (auto-configured by Vercel):

- `POSTGRES_URL`: PostgreSQL connection string
- `POSTGRES_PRISMA_URL`: Prisma-compatible connection string
- `POSTGRES_URL_NON_POOLING`: Non-pooling connection string
- `POSTGRES_USER`: Database user
- `POSTGRES_HOST`: Database host
- `POSTGRES_PASSWORD`: Database password
- `POSTGRES_DATABASE`: Database name
- `CRON_SECRET`: Secret key for securing cron endpoints

## Monitoring

- **Vercel Dashboard**: View deployment logs and cron job executions
- **Function Logs**: Monitor API performance and errors
- **Database Analytics**: Track query performance in Vercel Postgres dashboard

## Legacy Python Version

The original Python/Docker version is still available in the repository. See the `scripts/` folder for the Python implementation. The Next.js version provides:

- ✅ Better performance with PostgreSQL full-text search
- ✅ Automated cron jobs without manual setup
- ✅ Modern React UI with autocomplete
- ✅ One-click deployment to Vercel
- ✅ Scalable serverless architecture

## License

MIT

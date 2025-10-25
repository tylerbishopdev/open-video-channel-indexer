# Open.Video Channel Indexer

A Docker-based tool to create a searchable SQLite database of all channels on open.video.

## Features

- 🔍 **Full-text search** across channel names, handles, and descriptions
- 📊 **Statistics** on channels and video counts
- 💾 **Persistent SQLite database** with volume mounting
- 📤 **JSON export** for data portability
- 🐳 **Dockerized** for easy deployment

## Project Structure

```
open-video-channel-indexer/
├── Dockerfile              # Python environment setup
├── docker-compose.yml      # Container orchestration
├── requirements.txt        # Python dependencies
├── scripts/
│   └── indexer.py         # Main indexer script
└── data/
    └── open_video_channels.db  # SQLite database (created on first run)
```

## Quick Start

### 1. Build and Start Container

```bash
cd /Users/shibasafe/EzoicProject/open-video-channel-indexer
docker-compose up -d --build
```

### 2. Run Commands

Execute commands inside the container:

```bash
# Test with first 10 channels
docker exec -it open-video-indexer python scripts/indexer.py index 10

# Index all channels (takes ~30 minutes for 1000+ channels)
docker exec -it open-video-indexer python scripts/indexer.py index

# View statistics
docker exec -it open-video-indexer python scripts/indexer.py stats

# Search for channels
docker exec -it open-video-indexer python scripts/indexer.py search "cooking"

# Export to JSON
docker exec -it open-video-indexer python scripts/indexer.py export
```

### 3. Access Database Directly

```bash
# Enter container shell
docker exec -it open-video-indexer bash

# Access SQLite database
sqlite3 /app/data/open_video_channels.db

# Example queries:
SELECT COUNT(*) FROM channels;
SELECT * FROM channels WHERE video_count > 100 ORDER BY video_count DESC LIMIT 10;
```

## Commands

### Index Channels

```bash
# Index first N channels (for testing)
docker exec -it open-video-indexer python scripts/indexer.py index 50

# Index all channels from sitemap
docker exec -it open-video-indexer python scripts/indexer.py index
```

### Search Channels

```bash
# Search by keyword
docker exec -it open-video-indexer python scripts/indexer.py search "recipes"
docker exec -it open-video-indexer python scripts/indexer.py search "gaming"
docker exec -it open-video-indexer python scripts/indexer.py search "news"
```

### View Statistics

```bash
docker exec -it open-video-indexer python scripts/indexer.py stats
```

### Export Data

```bash
# Export to default location (/app/data/channels_index.json)
docker exec -it open-video-indexer python scripts/indexer.py export

# Copy exported JSON to host
docker cp open-video-indexer:/app/data/channels_index.json ./data/
```

## Database Schema

### Main Table: `channels`

| Column          | Type      | Description                    |
|-----------------|-----------|--------------------------------|
| id              | INTEGER   | Primary key                    |
| channel_handle  | TEXT      | Channel handle (e.g., @name)   |
| channel_url     | TEXT      | Full channel URL               |
| channel_name    | TEXT      | Display name                   |
| video_count     | INTEGER   | Number of videos               |
| join_date       | TEXT      | Channel creation date          |
| last_modified   | TEXT      | Last sitemap update            |
| logo_url        | TEXT      | Profile image URL              |
| description     | TEXT      | Channel description            |
| scraped_at      | TIMESTAMP | When data was indexed          |

### FTS Table: `channels_fts`

Full-text search index for fast querying.

## Data Persistence

The SQLite database is stored in `./data/` directory which is mounted as a Docker volume. This means:

- ✅ Data persists across container restarts
- ✅ Database is accessible from host machine
- ✅ Can be backed up easily

## Performance

- **Indexing speed**: ~2 requests/second (0.5s rate limit)
- **Estimated time**: ~8-10 minutes for 1000 channels
- **Database size**: ~500KB per 100 channels

## Maintenance

### Stop Container

```bash
docker-compose down
```

### Rebuild After Changes

```bash
docker-compose up -d --build
```

### View Logs

```bash
docker logs open-video-indexer
```

### Backup Database

```bash
cp ./data/open_video_channels.db ./data/backup_$(date +%Y%m%d).db
```

## Troubleshooting

### Container won't start

```bash
docker-compose logs
```

### Database locked

Stop and restart the container:
```bash
docker-compose restart
```

### Reset database

```bash
rm ./data/open_video_channels.db
docker-compose restart
```

## Advanced Usage

### Custom SQL Queries

```bash
docker exec -it open-video-indexer sqlite3 /app/data/open_video_channels.db

# Top channels by video count
SELECT channel_name, video_count FROM channels
WHERE video_count IS NOT NULL
ORDER BY video_count DESC LIMIT 20;

# Search with wildcards
SELECT * FROM channels WHERE channel_name LIKE '%cook%';

# Channels joined in 2024
SELECT * FROM channels WHERE join_date LIKE '%2024%';
```

### Programmatic Access

Since the database is in `./data/`, you can access it from other Python scripts:

```python
import sqlite3

conn = sqlite3.connect('./data/open_video_channels.db')
cursor = conn.cursor()
cursor.execute('SELECT * FROM channels WHERE video_count > 100')
results = cursor.fetchall()
```

## License

MIT

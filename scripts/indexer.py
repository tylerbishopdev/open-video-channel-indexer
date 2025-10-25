#!/usr/bin/env python3
"""
Open.Video Channel Indexer
Creates a searchable SQLite database of all channels on open.video
"""

import sqlite3
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import time
import json
import os
from datetime import datetime
from urllib.parse import urlparse
import re

class OpenVideoIndexer:
    def __init__(self, db_path=None):
        self.db_path = db_path or os.getenv('DB_PATH', '/app/data/open_video_channels.db')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        self.setup_database()

    def setup_database(self):
        """Create SQLite database with full-text search"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Main channels table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_handle TEXT UNIQUE,
                channel_url TEXT,
                channel_name TEXT,
                video_count INTEGER,
                join_date TEXT,
                last_modified TEXT,
                logo_url TEXT,
                description TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create full-text search virtual table
        cursor.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS channels_fts USING fts5(
                channel_handle,
                channel_name,
                description,
                content='channels',
                content_rowid='id'
            )
        ''')

        # Triggers to keep FTS index in sync
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS channels_ai AFTER INSERT ON channels BEGIN
                INSERT INTO channels_fts(rowid, channel_handle, channel_name, description)
                VALUES (new.id, new.channel_handle, new.channel_name, new.description);
            END
        ''')

        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS channels_ad AFTER DELETE ON channels BEGIN
                DELETE FROM channels_fts WHERE rowid = old.id;
            END
        ''')

        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS channels_au AFTER UPDATE ON channels BEGIN
                UPDATE channels_fts SET
                    channel_handle = new.channel_handle,
                    channel_name = new.channel_name,
                    description = new.description
                WHERE rowid = new.id;
            END
        ''')

        conn.commit()
        conn.close()
        print(f"✓ Database initialized: {self.db_path}")

    def fetch_sitemap(self, url):
        """Fetch and parse XML sitemap"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return ET.fromstring(response.content)
        except Exception as e:
            print(f"✗ Error fetching sitemap: {e}")
            return None

    def extract_channels_from_sitemap(self):
        """Extract all channel URLs from the sitemap"""
        print("\n📥 Fetching channels sitemap...")
        root = self.fetch_sitemap('https://open.video/channels-sitemap.xml')

        if root is None:
            return []

        channels = []
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

        for url in root.findall('.//ns:url', namespace):
            loc = url.find('ns:loc', namespace)
            lastmod = url.find('ns:lastmod', namespace)

            if loc is not None:
                channel_url = loc.text
                last_modified = lastmod.text if lastmod is not None else None

                # Extract channel handle from URL
                handle = channel_url.rstrip('/').split('/')[-1]

                channels.append({
                    'url': channel_url,
                    'handle': handle,
                    'last_modified': last_modified
                })

        print(f"✓ Found {len(channels)} channels in sitemap")
        return channels

    def scrape_channel_metadata(self, channel_url):
        """Scrape metadata from a channel page"""
        try:
            response = self.session.get(channel_url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            metadata = {}

            # Extract channel name
            name_elem = soup.find('h1') or soup.find('title')
            metadata['name'] = name_elem.get_text(strip=True) if name_elem else None

            # Extract video count (look for video-count div first, then fallback)
            video_count = None
            video_count_elem = soup.find('div', class_='video-count')
            if video_count_elem:
                text = video_count_elem.get_text(strip=True)
                match = re.search(r'(\d+)', text)
                if match:
                    video_count = int(match.group(1))

            # Fallback: look for p tag with video count (exclude page title)
            if video_count is None:
                for p in soup.find_all('p'):
                    text = p.get_text(strip=True)
                    if re.match(r'^\d+\s*videos?$', text, re.I):
                        match = re.search(r'(\d+)', text)
                        if match:
                            video_count = int(match.group(1))
                            break

            metadata['video_count'] = video_count

            # Extract join date
            join_date = None
            join_text = soup.find(string=re.compile(r'joined|join date', re.I))
            if join_text:
                # Look for date patterns
                date_match = re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d+,?\s+\d{4}', join_text, re.I)
                if date_match:
                    join_date = date_match.group(0)
            metadata['join_date'] = join_date

            # Extract logo URL
            logo = soup.find('img', {'class': re.compile(r'logo|avatar|profile', re.I)})
            metadata['logo_url'] = logo.get('src') if logo else None

            # Extract description
            desc = soup.find('meta', {'name': 'description'}) or soup.find('meta', {'property': 'og:description'})
            metadata['description'] = desc.get('content') if desc else None

            return metadata

        except Exception as e:
            print(f"  ⚠ Error scraping {channel_url}: {e}")
            return None

    def index_channels(self, rate_limit=0.5, max_channels=None):
        """Main indexing function"""
        print("\n" + "="*60)
        print("🚀 Starting Open.Video Channel Indexing")
        print("="*60)

        # Get all channels from sitemap
        channels = self.extract_channels_from_sitemap()

        if max_channels:
            channels = channels[:max_channels]
            print(f"⚠ Limited to first {max_channels} channels for testing")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        indexed_count = 0
        skipped_count = 0
        error_count = 0

        print(f"\n📊 Processing {len(channels)} channels...")
        print(f"⏱️  Rate limit: {rate_limit}s between requests\n")

        for i, channel in enumerate(channels, 1):
            handle = channel['handle']
            url = channel['url']

            # Check if already indexed
            cursor.execute('SELECT id FROM channels WHERE channel_handle = ?', (handle,))
            if cursor.fetchone():
                skipped_count += 1
                if i % 50 == 0:
                    print(f"  [{i}/{len(channels)}] Skipped (already indexed): {handle}")
                continue

            # Scrape metadata
            print(f"  [{i}/{len(channels)}] Scraping: {handle}...", end=' ')
            metadata = self.scrape_channel_metadata(url)

            if metadata:
                cursor.execute('''
                    INSERT INTO channels (
                        channel_handle, channel_url, channel_name, video_count,
                        join_date, last_modified, logo_url, description
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    handle,
                    url,
                    metadata.get('name'),
                    metadata.get('video_count'),
                    metadata.get('join_date'),
                    channel['last_modified'],
                    metadata.get('logo_url'),
                    metadata.get('description')
                ))
                conn.commit()
                indexed_count += 1
                print(f"✓ ({metadata.get('video_count', 0)} videos)")
            else:
                error_count += 1
                print("✗")

            # Rate limiting
            time.sleep(rate_limit)

            # Progress checkpoint every 100 channels
            if i % 100 == 0:
                print(f"\n  💾 Checkpoint: {indexed_count} indexed, {skipped_count} skipped, {error_count} errors\n")

        conn.close()

        print("\n" + "="*60)
        print("✅ INDEXING COMPLETE")
        print("="*60)
        print(f"  ✓ Indexed: {indexed_count}")
        print(f"  ⊘ Skipped: {skipped_count}")
        print(f"  ✗ Errors: {error_count}")
        print(f"  📁 Database: {self.db_path}")
        print("="*60 + "\n")

    def search(self, query, limit=20):
        """Search channels by name, handle, or description"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Full-text search
        cursor.execute('''
            SELECT c.channel_handle, c.channel_name, c.video_count,
                   c.join_date, c.channel_url, c.description
            FROM channels c
            JOIN channels_fts fts ON c.id = fts.rowid
            WHERE channels_fts MATCH ?
            ORDER BY c.video_count DESC
            LIMIT ?
        ''', (query, limit))

        results = cursor.fetchall()
        conn.close()

        return results

    def export_to_json(self, output_file='/app/data/channels_index.json'):
        """Export entire index to JSON"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT channel_handle, channel_url, channel_name, video_count,
                   join_date, last_modified, logo_url, description
            FROM channels
            ORDER BY video_count DESC
        ''')

        channels = []
        for row in cursor.fetchall():
            channels.append({
                'handle': row[0],
                'url': row[1],
                'name': row[2],
                'video_count': row[3],
                'join_date': row[4],
                'last_modified': row[5],
                'logo_url': row[6],
                'description': row[7]
            })

        with open(output_file, 'w') as f:
            json.dump(channels, f, indent=2)

        conn.close()
        print(f"✓ Exported {len(channels)} channels to {output_file}")

    def stats(self):
        """Display database statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM channels')
        total = cursor.fetchone()[0]

        cursor.execute('SELECT SUM(video_count) FROM channels WHERE video_count IS NOT NULL')
        total_videos = cursor.fetchone()[0] or 0

        cursor.execute('SELECT AVG(video_count) FROM channels WHERE video_count IS NOT NULL')
        avg_videos = cursor.fetchone()[0] or 0

        cursor.execute('''
            SELECT channel_handle, channel_name, video_count
            FROM channels
            WHERE video_count IS NOT NULL
            ORDER BY video_count DESC
            LIMIT 10
        ''')
        top_channels = cursor.fetchall()

        conn.close()

        print("\n" + "="*60)
        print("📊 DATABASE STATISTICS")
        print("="*60)
        print(f"Total Channels: {total:,}")
        print(f"Total Videos: {total_videos:,}")
        print(f"Average Videos per Channel: {avg_videos:.1f}")
        print("\nTop 10 Channels by Video Count:")
        print("-" * 60)
        for handle, name, count in top_channels:
            name_display = name if name else handle
            print(f"  {name_display[:40]:40} {count:>6} videos")
        print("="*60 + "\n")


def main():
    """Interactive CLI"""
    import sys

    indexer = OpenVideoIndexer()

    if len(sys.argv) < 2:
        print("""
Open.Video Channel Indexer
===========================

Usage:
  python indexer.py index [max_channels]  - Index channels from sitemap
  python indexer.py search <query>        - Search indexed channels
  python indexer.py stats                 - Show database statistics
  python indexer.py export [filename]     - Export to JSON

Examples:
  python indexer.py index 50              - Index first 50 channels (testing)
  python indexer.py index                 - Index all channels
  python indexer.py search "cooking"      - Search for cooking channels
  python indexer.py stats                 - View database stats
        """)
        return

    command = sys.argv[1]

    if command == 'index':
        max_channels = int(sys.argv[2]) if len(sys.argv) > 2 else None
        indexer.index_channels(rate_limit=0.5, max_channels=max_channels)

    elif command == 'search':
        if len(sys.argv) < 3:
            print("Error: Please provide a search query")
            return

        query = ' '.join(sys.argv[2:])
        results = indexer.search(query)

        print(f"\n🔍 Search results for: '{query}'")
        print("="*80)

        if results:
            for handle, name, video_count, join_date, url, desc in results:
                print(f"\n@{handle}")
                if name:
                    print(f"  Name: {name}")
                if video_count:
                    print(f"  Videos: {video_count:,}")
                if join_date:
                    print(f"  Joined: {join_date}")
                print(f"  URL: {url}")
                if desc:
                    print(f"  Description: {desc[:100]}...")
        else:
            print("No results found")

        print("="*80 + "\n")

    elif command == 'stats':
        indexer.stats()

    elif command == 'export':
        output = sys.argv[2] if len(sys.argv) > 2 else '/app/data/channels_index.json'
        indexer.export_to_json(output)

    else:
        print(f"Unknown command: {command}")


if __name__ == '__main__':
    main()

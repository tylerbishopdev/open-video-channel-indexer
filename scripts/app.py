#!/usr/bin/env python3
"""
Flask web server for Open.Video Channel Search
Provides API endpoints and serves frontend
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import psycopg2
import psycopg2.extras
import os
import re

# Import the indexer class
from scripts.indexer import OpenVideoIndexer

app = Flask(__name__, static_folder='../static')
CORS(app)

def get_db_conn():
    """Get PostgreSQL database connection."""
    db_url = os.getenv('POSTGRES_URL')
    if not db_url:
        raise ValueError("POSTGRES_URL environment variable is not set.")
    conn = psycopg2.connect(db_url)
    return conn

@app.route('/')
def index():
    """Serve the main search page"""
    return send_from_directory('../static', 'index.html')

@app.route('/api/search')
def search():
    """Full search endpoint"""
    query = request.args.get('q', '')
    limit = request.args.get('limit', 20, type=int)

    if not query:
        return jsonify({'results': [], 'count': 0})

    conn = get_db_conn()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    # Sanitize query for tsquery
    # Replace special characters with spaces and use '|' for OR logic
    sanitized_query = re.sub(r'[!\'()|&]', ' ', query).strip()
    ts_query = ' | '.join(sanitized_query.split())

    try:
        cursor.execute('''
            SELECT channel_handle, channel_name, video_count,
                   join_date, channel_url, description, logo_url
            FROM channels
            WHERE fts_document @@ to_tsquery('english', %s)
            ORDER BY video_count DESC NULLS LAST
            LIMIT %s
        ''', (ts_query, limit))
        
        results = [dict(row) for row in cursor.fetchall()]

    except Exception as e:
        print(f"FTS search failed: {e}")
        # Fallback to LIKE search if FTS fails
        search_pattern = f'%{query}%'
        cursor.execute('''
            SELECT channel_handle, channel_name, video_count,
                   join_date, channel_url, description, logo_url
            FROM channels
            WHERE channel_name ILIKE %s
               OR channel_handle ILIKE %s
               OR description ILIKE %s
            ORDER BY video_count DESC NULLS LAST
            LIMIT %s
        ''', (search_pattern, search_pattern, search_pattern, limit))
        results = [dict(row) for row in cursor.fetchall()]

    finally:
        cursor.close()
        conn.close()

    return jsonify({
        'results': results,
        'count': len(results),
        'query': query
    })

@app.route('/api/autocomplete')
def autocomplete():
    """Autocomplete endpoint"""
    query = request.args.get('q', '').strip()
    limit = request.args.get('limit', 10, type=int)

    if not query or len(query) < 2:
        return jsonify({'suggestions': []})

    conn = get_db_conn()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    try:
        search_pattern = f'%{query}%'
        cursor.execute('''
            SELECT DISTINCT channel_name, channel_handle, video_count
            FROM channels
            WHERE channel_name ILIKE %s OR channel_handle ILIKE %s
            ORDER BY video_count DESC NULLS LAST
            LIMIT %s
        ''', (search_pattern, search_pattern, limit))

        suggestions = []
        for row in cursor.fetchall():
            name = row['channel_name'] or row['channel_handle']
            suggestions.append({
                'text': name,
                'handle': row['channel_handle'],
                'video_count': row['video_count']
            })

        return jsonify({'suggestions': suggestions})

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/stats')
def stats():
    """Get database statistics"""
    conn = get_db_conn()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    try:
        cursor.execute('SELECT COUNT(*) as total FROM channels')
        total = cursor.fetchone()['total']

        cursor.execute('SELECT SUM(video_count) as total FROM channels WHERE video_count IS NOT NULL')
        total_videos = cursor.fetchone()['total'] or 0

        cursor.execute('SELECT AVG(video_count) as avg FROM channels WHERE video_count IS NOT NULL')
        avg_videos = cursor.fetchone()['avg'] or 0

        return jsonify({
            'total_channels': total,
            'total_videos': int(total_videos),
            'avg_videos_per_channel': round(float(avg_videos), 1)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})

@app.route('/api/cron/index')
def cron_index():
    """Cron job endpoint to trigger channel indexing."""
    if os.getenv('VERCEL_ENV') != 'production' and not os.getenv('CRON_SECRET'):
        return jsonify({'error': 'Not authorized'}), 401
    
    if os.getenv('CRON_SECRET') and request.headers.get('Authorization') != f"Bearer {os.getenv('CRON_SECRET')}":
         return jsonify({'error': 'Not authorized'}), 401

    max_channels_str = request.args.get('max')
    max_channels = int(max_channels_str) if max_channels_str and max_channels_str.isdigit() else None

    try:
        indexer = OpenVideoIndexer()
        indexer.index_channels(rate_limit=0.2, max_channels=max_channels)
        return jsonify({'status': 'success', 'message': f'Indexing triggered for up to {max_channels or "all"} channels.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

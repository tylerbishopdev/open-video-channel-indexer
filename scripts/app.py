#!/usr/bin/env python3
"""
Flask web server for Open.Video Channel Search
Provides API endpoints and serves frontend
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import sqlite3
import os

app = Flask(__name__, static_folder='../static')
CORS(app)

DB_PATH = os.getenv('DB_PATH', '/app/data/open_video_channels.db')

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    """Serve the main search page"""
    return send_from_directory('../static', 'index.html')

@app.route('/api/search')
def search():
    """
    Full search endpoint
    Query params:
        q: search query
        limit: max results (default 20)
    """
    query = request.args.get('q', '')
    limit = request.args.get('limit', 20, type=int)

    if not query:
        return jsonify({'results': [], 'count': 0})

    conn = get_db()
    cursor = conn.cursor()

    results = []

    try:
        # Try FTS search with quoted query (handles special chars)
        # Quote the entire query to treat it as a phrase
        fts_query = f'"{query}"'

        cursor.execute('''
            SELECT c.channel_handle, c.channel_name, c.video_count,
                   c.join_date, c.channel_url, c.description, c.logo_url
            FROM channels c
            JOIN channels_fts fts ON c.id = fts.rowid
            WHERE channels_fts MATCH ?
            ORDER BY c.video_count DESC
            LIMIT ?
        ''', (fts_query, limit))

        for row in cursor.fetchall():
            results.append({
                'handle': row['channel_handle'],
                'name': row['channel_name'],
                'video_count': row['video_count'],
                'join_date': row['join_date'],
                'url': row['channel_url'],
                'description': row['description'],
                'logo_url': row['logo_url']
            })

    except Exception:
        # Fallback to LIKE search if FTS fails
        pass

    # If no FTS results or FTS failed, try LIKE search as fallback
    if not results:
        try:
            search_pattern = f'%{query}%'
            cursor.execute('''
                SELECT channel_handle, channel_name, video_count,
                       join_date, channel_url, description, logo_url
                FROM channels
                WHERE channel_name LIKE ?
                   OR channel_handle LIKE ?
                   OR description LIKE ?
                ORDER BY video_count DESC
                LIMIT ?
            ''', (search_pattern, search_pattern, search_pattern, limit))

            for row in cursor.fetchall():
                results.append({
                    'handle': row['channel_handle'],
                    'name': row['channel_name'],
                    'video_count': row['video_count'],
                    'join_date': row['join_date'],
                    'url': row['channel_url'],
                    'description': row['description'],
                    'logo_url': row['logo_url']
                })
        except Exception as e:
            conn.close()
            return jsonify({'error': str(e)}), 500

    conn.close()

    return jsonify({
        'results': results,
        'count': len(results),
        'query': query
    })

@app.route('/api/autocomplete')
def autocomplete():
    """
    Autocomplete endpoint for search suggestions
    Query params:
        q: partial query
        limit: max suggestions (default 10)
    """
    query = request.args.get('q', '').strip()
    limit = request.args.get('limit', 10, type=int)

    if not query or len(query) < 2:
        return jsonify({'suggestions': []})

    conn = get_db()
    cursor = conn.cursor()

    try:
        # Search for matching channel names and handles
        cursor.execute('''
            SELECT DISTINCT channel_name, channel_handle, video_count
            FROM channels
            WHERE channel_name LIKE ? OR channel_handle LIKE ?
            ORDER BY video_count DESC
            LIMIT ?
        ''', (f'%{query}%', f'%{query}%', limit))

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
        conn.close()

@app.route('/api/stats')
def stats():
    """Get database statistics"""
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT COUNT(*) as total FROM channels')
        total = cursor.fetchone()['total']

        cursor.execute('SELECT SUM(video_count) as total FROM channels WHERE video_count IS NOT NULL')
        total_videos = cursor.fetchone()['total'] or 0

        cursor.execute('SELECT AVG(video_count) as avg FROM channels WHERE video_count IS NOT NULL')
        avg_videos = cursor.fetchone()['avg'] or 0

        return jsonify({
            'total_channels': total,
            'total_videos': total_videos,
            'avg_videos_per_channel': round(avg_videos, 1)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'database': DB_PATH})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

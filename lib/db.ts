import { sql } from '@vercel/postgres';

export interface Channel {
  id: number;
  channel_handle: string;
  channel_url: string;
  channel_name: string | null;
  video_count: number | null;
  join_date: string | null;
  last_modified: string | null;
  logo_url: string | null;
  description: string | null;
  scraped_at: Date;
}

/**
 * Initialize database tables and indexes
 */
export async function initializeDatabase() {
  try {
    // Create channels table
    await sql`
      CREATE TABLE IF NOT EXISTS channels (
        id SERIAL PRIMARY KEY,
        channel_handle TEXT UNIQUE NOT NULL,
        channel_url TEXT,
        channel_name TEXT,
        video_count INTEGER,
        join_date TEXT,
        last_modified TEXT,
        logo_url TEXT,
        description TEXT,
        scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        search_vector tsvector
      )
    `;

    // Create search vector index for full-text search
    await sql`
      CREATE INDEX IF NOT EXISTS channels_search_idx
      ON channels USING GIN (search_vector)
    `;

    // Create index on video_count for sorting
    await sql`
      CREATE INDEX IF NOT EXISTS channels_video_count_idx
      ON channels (video_count DESC NULLS LAST)
    `;

    // Create trigger to update search_vector automatically
    await sql`
      CREATE OR REPLACE FUNCTION update_search_vector()
      RETURNS TRIGGER AS $$
      BEGIN
        NEW.search_vector :=
          setweight(to_tsvector('english', COALESCE(NEW.channel_handle, '')), 'A') ||
          setweight(to_tsvector('english', COALESCE(NEW.channel_name, '')), 'A') ||
          setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'B');
        RETURN NEW;
      END;
      $$ LANGUAGE plpgsql;
    `;

    await sql`
      DROP TRIGGER IF EXISTS channels_search_update ON channels;
    `;

    await sql`
      CREATE TRIGGER channels_search_update
      BEFORE INSERT OR UPDATE ON channels
      FOR EACH ROW
      EXECUTE FUNCTION update_search_vector();
    `;

    console.log('✅ Database initialized successfully');
    return { success: true };
  } catch (error) {
    console.error('❌ Error initializing database:', error);
    throw error;
  }
}

/**
 * Search channels using full-text search
 */
export async function searchChannels(query: string, limit: number = 20) {
  try {
    const searchQuery = query.trim().split(/\s+/).join(' & ');

    const { rows } = await sql`
      SELECT
        channel_handle,
        channel_name,
        video_count,
        join_date,
        channel_url,
        description,
        logo_url,
        ts_rank(search_vector, to_tsquery('english', ${searchQuery})) as rank
      FROM channels
      WHERE search_vector @@ to_tsquery('english', ${searchQuery})
      ORDER BY rank DESC, video_count DESC NULLS LAST
      LIMIT ${limit}
    `;

    return rows;
  } catch (error) {
    // Fallback to LIKE search if full-text search fails
    const pattern = `%${query}%`;
    const { rows } = await sql`
      SELECT
        channel_handle,
        channel_name,
        video_count,
        join_date,
        channel_url,
        description,
        logo_url
      FROM channels
      WHERE
        channel_name ILIKE ${pattern}
        OR channel_handle ILIKE ${pattern}
        OR description ILIKE ${pattern}
      ORDER BY video_count DESC NULLS LAST
      LIMIT ${limit}
    `;

    return rows;
  }
}

/**
 * Get autocomplete suggestions
 */
export async function getAutocompleteSuggestions(query: string, limit: number = 10) {
  const pattern = `%${query}%`;

  const { rows } = await sql`
    SELECT DISTINCT
      channel_name,
      channel_handle,
      video_count
    FROM channels
    WHERE
      channel_name ILIKE ${pattern}
      OR channel_handle ILIKE ${pattern}
    ORDER BY video_count DESC NULLS LAST
    LIMIT ${limit}
  `;

  return rows;
}

/**
 * Get database statistics
 */
export async function getDatabaseStats() {
  const { rows: totalRows } = await sql`
    SELECT COUNT(*) as total FROM channels
  `;

  const { rows: videoRows } = await sql`
    SELECT
      COALESCE(SUM(video_count), 0) as total,
      COALESCE(AVG(video_count), 0) as avg
    FROM channels
    WHERE video_count IS NOT NULL
  `;

  return {
    total_channels: Number(totalRows[0].total),
    total_videos: Number(videoRows[0].total),
    avg_videos_per_channel: Number(videoRows[0].avg).toFixed(1),
  };
}

/**
 * Insert or update a channel
 */
export async function upsertChannel(channel: {
  handle: string;
  url: string;
  name: string | null;
  video_count: number | null;
  join_date: string | null;
  last_modified: string | null;
  logo_url: string | null;
  description: string | null;
}) {
  const { rows } = await sql`
    INSERT INTO channels (
      channel_handle,
      channel_url,
      channel_name,
      video_count,
      join_date,
      last_modified,
      logo_url,
      description
    ) VALUES (
      ${channel.handle},
      ${channel.url},
      ${channel.name},
      ${channel.video_count},
      ${channel.join_date},
      ${channel.last_modified},
      ${channel.logo_url},
      ${channel.description}
    )
    ON CONFLICT (channel_handle)
    DO UPDATE SET
      channel_url = EXCLUDED.channel_url,
      channel_name = EXCLUDED.channel_name,
      video_count = EXCLUDED.video_count,
      join_date = EXCLUDED.join_date,
      last_modified = EXCLUDED.last_modified,
      logo_url = EXCLUDED.logo_url,
      description = EXCLUDED.description,
      scraped_at = CURRENT_TIMESTAMP
    RETURNING id
  `;

  return rows[0];
}

/**
 * Check if channel exists
 */
export async function channelExists(handle: string): Promise<boolean> {
  const { rows } = await sql`
    SELECT 1 FROM channels WHERE channel_handle = ${handle} LIMIT 1
  `;

  return rows.length > 0;
}

import { XMLParser } from 'fast-xml-parser';
import * as cheerio from 'cheerio';

export interface SitemapChannel {
  url: string;
  handle: string;
  last_modified: string | null;
}

export interface ChannelMetadata {
  name: string | null;
  video_count: number | null;
  join_date: string | null;
  logo_url: string | null;
  description: string | null;
}

/**
 * Fetch and parse the channels sitemap
 */
export async function fetchChannelsSitemap(): Promise<SitemapChannel[]> {
  try {
    const response = await fetch('https://open.video/channels-sitemap.xml', {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch sitemap: ${response.status}`);
    }

    const xmlText = await response.text();
    const parser = new XMLParser();
    const result = parser.parse(xmlText);

    const channels: SitemapChannel[] = [];
    const urlset = result.urlset || result;
    const urls = Array.isArray(urlset.url) ? urlset.url : [urlset.url];

    for (const url of urls) {
      if (!url || !url.loc) continue;

      const channelUrl = url.loc;
      const handle = channelUrl.replace(/\/$/, '').split('/').pop() || '';
      const lastModified = url.lastmod || null;

      channels.push({
        url: channelUrl,
        handle: handle,
        last_modified: lastModified,
      });
    }

    console.log(`✅ Found ${channels.length} channels in sitemap`);
    return channels;
  } catch (error) {
    console.error('❌ Error fetching sitemap:', error);
    throw error;
  }
}

/**
 * Scrape metadata from a channel page
 */
export async function scrapeChannelMetadata(channelUrl: string): Promise<ChannelMetadata | null> {
  try {
    const response = await fetch(channelUrl, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
      },
      signal: AbortSignal.timeout(15000), // 15 second timeout
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const html = await response.text();
    const $ = cheerio.load(html);

    // Extract channel name
    const nameElem = $('h1').first().text().trim() || $('title').first().text().trim() || null;

    // Extract video count
    let videoCount: number | null = null;
    const videoCountElem = $('.video-count').first().text();
    if (videoCountElem) {
      const match = videoCountElem.match(/(\d+)/);
      if (match) videoCount = parseInt(match[1], 10);
    }

    // Fallback: look for p tag with video count
    if (videoCount === null) {
      $('p').each((_, elem) => {
        const text = $(elem).text().trim();
        if (/^\d+\s*videos?$/i.test(text)) {
          const match = text.match(/(\d+)/);
          if (match) {
            videoCount = parseInt(match[1], 10);
            return false; // break
          }
        }
      });
    }

    // Extract join date
    let joinDate: string | null = null;
    const bodyText = $.text();
    const dateMatch = bodyText.match(/(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d+,?\s+\d{4}/i);
    if (dateMatch) {
      joinDate = dateMatch[0];
    }

    // Extract logo URL
    const logoElem = $('img[class*="logo"], img[class*="avatar"], img[class*="profile"]').first();
    const logoUrl = logoElem.attr('src') || null;

    // Extract description
    const descMeta = $('meta[name="description"]').attr('content') ||
                     $('meta[property="og:description"]').attr('content') || null;

    return {
      name: nameElem,
      video_count: videoCount,
      join_date: joinDate,
      logo_url: logoUrl,
      description: descMeta,
    };
  } catch (error: any) {
    console.error(`⚠️  Error scraping ${channelUrl}:`, error.message);
    return null;
  }
}

/**
 * Sleep utility for rate limiting
 */
export function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

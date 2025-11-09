import { NextRequest, NextResponse } from 'next/server';
import { fetchChannelsSitemap, scrapeChannelMetadata, sleep } from '@/lib/scraper';
import { upsertChannel, channelExists } from '@/lib/db';

export const maxDuration = 300; // 5 minutes max execution for Vercel Serverless
export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  try {
    // Verify cron secret for security
    const authHeader = request.headers.get('authorization');
    const cronSecret = process.env.CRON_SECRET;

    if (cronSecret && authHeader !== `Bearer ${cronSecret}`) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const searchParams = request.nextUrl.searchParams;
    const maxChannels = parseInt(searchParams.get('max') || '100', 10);
    const rateLimit = parseInt(searchParams.get('rate') || '500', 10); // ms between requests

    console.log(`🚀 Starting channel indexing (max: ${maxChannels})`);

    // Fetch channels from sitemap
    const channels = await fetchChannelsSitemap();
    const channelsToProcess = channels.slice(0, maxChannels);

    let indexed = 0;
    let skipped = 0;
    let errors = 0;

    for (const channel of channelsToProcess) {
      try {
        // Check if already indexed
        const exists = await channelExists(channel.handle);
        if (exists) {
          skipped++;
          continue;
        }

        // Scrape metadata
        const metadata = await scrapeChannelMetadata(channel.url);

        if (metadata) {
          await upsertChannel({
            handle: channel.handle,
            url: channel.url,
            name: metadata.name,
            video_count: metadata.video_count,
            join_date: metadata.join_date,
            last_modified: channel.last_modified,
            logo_url: metadata.logo_url,
            description: metadata.description,
          });

          indexed++;
          console.log(`✅ Indexed: ${channel.handle} (${metadata.video_count || 0} videos)`);
        } else {
          errors++;
          console.log(`❌ Failed to scrape: ${channel.handle}`);
        }

        // Rate limiting
        await sleep(rateLimit);
      } catch (error: any) {
        errors++;
        console.error(`❌ Error processing ${channel.handle}:`, error.message);
      }
    }

    return NextResponse.json({
      success: true,
      indexed,
      skipped,
      errors,
      total_processed: channelsToProcess.length,
    });
  } catch (error: any) {
    console.error('❌ Indexing error:', error);
    return NextResponse.json(
      {
        success: false,
        error: error.message || 'Indexing failed',
      },
      { status: 500 }
    );
  }
}

import { NextRequest, NextResponse } from 'next/server';
import { getAutocompleteSuggestions } from '@/lib/db';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const query = searchParams.get('q')?.trim() || '';
    const limit = parseInt(searchParams.get('limit') || '10', 10);

    if (!query || query.length < 2) {
      return NextResponse.json({ suggestions: [] });
    }

    const suggestions = await getAutocompleteSuggestions(query, limit);

    return NextResponse.json({
      suggestions: suggestions.map(row => ({
        text: row.channel_name || row.channel_handle,
        handle: row.channel_handle,
        video_count: row.video_count,
      })),
    });
  } catch (error: any) {
    console.error('Autocomplete error:', error);
    return NextResponse.json(
      { error: error.message || 'Internal server error' },
      { status: 500 }
    );
  }
}

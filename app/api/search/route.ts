import { NextRequest, NextResponse } from 'next/server';
import { searchChannels } from '@/lib/db';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const query = searchParams.get('q') || '';
    const limit = parseInt(searchParams.get('limit') || '20', 10);

    if (!query) {
      return NextResponse.json({ results: [], count: 0 });
    }

    const results = await searchChannels(query, limit);

    return NextResponse.json({
      results,
      count: results.length,
      query,
    });
  } catch (error: any) {
    console.error('Search error:', error);
    return NextResponse.json(
      { error: error.message || 'Internal server error' },
      { status: 500 }
    );
  }
}

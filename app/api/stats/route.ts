import { NextResponse } from 'next/server';
import { getDatabaseStats } from '@/lib/db';

export async function GET() {
  try {
    const stats = await getDatabaseStats();
    return NextResponse.json(stats);
  } catch (error: any) {
    console.error('Stats error:', error);
    return NextResponse.json(
      { error: error.message || 'Internal server error' },
      { status: 500 }
    );
  }
}

import { NextRequest, NextResponse } from 'next/server';
import { initializeDatabase } from '@/lib/db';

export async function POST(request: NextRequest) {
  try {
    // Optional: Add authentication here for production
    const authHeader = request.headers.get('authorization');
    const cronSecret = process.env.CRON_SECRET;

    if (cronSecret && authHeader !== `Bearer ${cronSecret}`) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    await initializeDatabase();

    return NextResponse.json({
      success: true,
      message: 'Database initialized successfully',
    });
  } catch (error: any) {
    console.error('Database initialization error:', error);
    return NextResponse.json(
      { error: error.message || 'Failed to initialize database' },
      { status: 500 }
    );
  }
}

import { NextRequest, NextResponse } from 'next/server';
import { findRecipeNormalizedBySlug } from '@/lib/recipesFromFilesystem';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ slug: string }> }
) {
  try {
    const { slug } = await params;
    const recipe = findRecipeNormalizedBySlug(process.cwd(), slug);

    if (!recipe) {
      return NextResponse.json({ error: 'Recipe not found' }, { status: 404 });
    }

    return NextResponse.json({
      ...recipe,
      is_bookmarked: false,
      user_status: null,
      user_rating: null,
      context_labels: [],
    });
  } catch (error) {
    console.error('Error fetching recipe:', error);
    return NextResponse.json({ error: 'Failed to fetch recipe' }, { status: 500 });
  }
}

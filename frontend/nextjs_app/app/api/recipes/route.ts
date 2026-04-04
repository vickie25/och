import { NextRequest, NextResponse } from 'next/server';
import { loadAllRecipesNormalized } from '@/lib/recipesFromFilesystem';

export async function GET(request: NextRequest) {
  console.log('[API] Recipes GET request received:', request.url);

  try {
    const { searchParams } = new URL(request.url);
    const track = searchParams.get('track_code');
    const level = searchParams.get('level');
    const limit = parseInt(searchParams.get('limit') || '20');

    const userTrack = request.cookies.get('user_track')?.value;

    const recipeFiles = loadAllRecipesNormalized(process.cwd());

    let filteredRecipes = recipeFiles;

    if (track) {
      filteredRecipes = filteredRecipes.filter((recipe) => recipe.track_code === track);
    } else if (userTrack) {
      const userTrackRecipes = recipeFiles.filter((recipe) => recipe.track_code === userTrack);
      const otherTrackRecipes = recipeFiles.filter((recipe) => recipe.track_code !== userTrack);

      const limitedOtherRecipes: Record<string, unknown>[] = [];
      const tracks = Array.from(
        new Set(otherTrackRecipes.map((r) => r.track_code as string))
      );

      for (const otherTrack of tracks) {
        const trackRecipes = otherTrackRecipes.filter((r) => r.track_code === otherTrack);
        limitedOtherRecipes.push(...trackRecipes.slice(0, 2));
      }

      filteredRecipes = [...userTrackRecipes, ...limitedOtherRecipes];
    }

    if (level) {
      filteredRecipes = filteredRecipes.filter((recipe) => recipe.level === level);
    }

    filteredRecipes.sort(
      (a, b) =>
        new Date((b.created_at as string) || 0).getTime() -
        new Date((a.created_at as string) || 0).getTime()
    );

    const limitedRecipes = filteredRecipes.slice(0, limit);

    const formattedRecipes = limitedRecipes.map((recipe) => ({
      ...recipe,
      is_bookmarked: false,
      user_status: null,
      user_rating: null,
      context_labels: [],
      is_user_track: userTrack ? recipe.track_code === userTrack : true,
      track_access: userTrack
        ? recipe.track_code === userTrack
          ? 'full'
          : 'preview'
        : 'full',
    }));

    return NextResponse.json({
      recipes: formattedRecipes,
      total: filteredRecipes.length,
      page_size: limit,
    });
  } catch (error) {
    console.error('Error fetching recipes:', error);
    return NextResponse.json({ error: 'Failed to fetch recipes' }, { status: 500 });
  }
}

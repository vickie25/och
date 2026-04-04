/**
 * Recipe Engine TypeScript types
 */

export type RecipeDifficulty = 'beginner' | 'intermediate' | 'advanced' | 'mastery';

export type RecipeStatus = 'not_started' | 'in_progress' | 'completed';

export interface RecipeContentSection {
  type: 'intro' | 'prerequisites' | 'steps' | 'validation';
  title: string;
  content?: string;
  items?: string[];
  steps?: RecipeStep[];
}

export interface RecipeStep {
  step: number;
  title: string;
  commands?: string[];
  code?: string;
  explanation: string;
}

export interface Recipe {
  id: string;
  title: string;
  slug: string;
  summary: string;
  description?: string;
  difficulty: RecipeDifficulty;
  estimated_minutes: number;
  /** Next.js / file-based recipe JSON (optional; may mirror track_codes[0]) */
  track_code?: string;
  /** Level tier for filtering (Next API / OCH bundles) */
  level?: RecipeDifficulty | string;
  /** Alias used by some JSON seeds */
  expected_duration_minutes?: number;
  track_codes: string[];
  skill_codes: string[];
  tools_used: string[];
  prerequisites?: string[];
  content: {
    sections: RecipeContentSection[];
  };
  validation_steps?: Record<string, string>;
  thumbnail_url?: string;
  mentor_curated: boolean;
  usage_count: number;
  avg_rating: number;
  is_active: boolean;
  created_by?: string;
  created_at: string;
  updated_at: string;
  
  // User-specific fields (when fetched with user context)
  is_bookmarked?: boolean;
  user_status?: RecipeStatus;
  user_rating?: number;
}

export interface RecipeListResponse extends Recipe {
  is_bookmarked: boolean;
  status?: RecipeStatus | null;
  user_status: RecipeStatus | null;
  user_rating: number | null;
  context_labels?: string[]; // e.g., ["Used in Mission", "Used in Module"]
}

export interface UserRecipeProgress {
  id: string;
  recipe: string;
  recipe_title: string;
  recipe_slug: string;
  status: RecipeStatus;
  rating?: number;
  notes?: string;
  time_spent_minutes?: number;
  completed_at?: string;
  created_at: string;
  updated_at: string;
}

export interface RecipeContextLink {
  id: string;
  recipe: string;
  recipe_title: string;
  recipe_slug: string;
  recipe_summary: string;
  recipe_difficulty: RecipeDifficulty;
  recipe_estimated_minutes: number;
  context_type: 'mission' | 'module' | 'project' | 'mentor_session';
  context_id: string;
  is_required: boolean;
  position_order: number;
}

export interface RecipeBookmark {
  id: string;
  recipe: Recipe;
  bookmarked_at: string;
}

export interface RecipeProgressUpdate {
  status?: RecipeStatus;
  rating?: number | null;
  helpful_for?: string[];
  notes?: string;
  time_spent_minutes?: number | null;
}

export interface RecipeStats {
  total: number;
  bookmarked: number;
}

export interface RecipeFilters {
  search?: string;
  track?: string;
  /** Alias for `track` (Next `/api/recipes?track_code=`) */
  track_code?: string;
  /** Alias for `difficulty` (Next `/api/recipes?level=`) */
  level?: string;
  skill_code?: string;
  max_duration?: number;
  difficulty?: RecipeDifficulty;
  max_time?: number;
  context?: 'mission' | 'module' | 'project' | 'mentor_session';
  sort?: 'relevance' | 'popular' | 'recent' | 'rating';
}

/** Query shape from `useRecipeFilters` / coaching recipes URL */
export type RecipeQueryParams = {
  track_code?: string;
  level?: string;
  skill_code?: string | string[];
  max_duration?: number;
  search?: string;
  limit?: number;
};

/** In-app / push-style recipe notification payload */
export interface RecipeNotification {
  id?: string;
  title: string;
  body?: string;
  recipe_id?: string | number;
  type?: string;
  read?: boolean;
  created_at?: string;
}

export interface RecipeDetailResponse extends Recipe {
  is_bookmarked: boolean;
  user_progress?: {
    status: string;
    rating?: number;
    notes?: string;
    time_spent_minutes?: number;
    completed_at?: string;
  };
  related_recipes: Recipe[];
}



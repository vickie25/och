import fs from 'fs';
import path from 'path';

/** Recursively collect `.json` paths under `dir`, excluding `_index.json`. */
export function walkRecipeJsonFiles(dir: string, acc: string[] = []): string[] {
  if (!fs.existsSync(dir)) return acc;
  for (const name of fs.readdirSync(dir)) {
    const full = path.join(dir, name);
    const st = fs.statSync(full);
    if (st.isDirectory()) walkRecipeJsonFiles(full, acc);
    else if (name.endsWith('.json') && name !== '_index.json') acc.push(full);
  }
  return acc;
}

function mapTrackCode(t: string): string {
  const k = (t || '').trim().toLowerCase();
  if (k === 'defensive' || k === 'defender' || k === 'cyber_defense') return 'defender';
  if (['offensive', 'grc', 'innovation', 'leadership'].includes(k)) return k;
  return k || 'innovation';
}

function mapLevel(t: string): string {
  const k = (t || '').trim().toLowerCase();
  if (k === 'beginner') return 'beginner';
  if (k === 'intermediate') return 'intermediate';
  if (k === 'advanced') return 'advanced';
  if (k === 'mastery') return 'mastery';
  return 'beginner';
}

function parseEstimatedMinutes(raw: string | undefined): number {
  if (!raw) return 30;
  const s = String(raw).toLowerCase();
  const rangeMin = s.match(/(\d+)\s*-\s*(\d+)\s*min/);
  if (rangeMin) {
    return Math.round((parseInt(rangeMin[1], 10) + parseInt(rangeMin[2], 10)) / 2);
  }
  const min = s.match(/(\d+)\s*min/);
  if (min) return parseInt(min[1], 10);
  const rangeHr = s.match(/(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*hrs?/);
  if (rangeHr) {
    return Math.round(((parseFloat(rangeHr[1]) + parseFloat(rangeHr[2])) / 2) * 60);
  }
  const hr = s.match(/(\d+(?:\.\d+)?)\s*hrs?/);
  if (hr) return Math.round(parseFloat(hr[1]) * 60);
  return 30;
}

/**
 * Normalize OCH bundle recipe JSON or pass through canonical `data/recipes/*.json` shape.
 */
export function normalizeRecipeJson(
  raw: Record<string, unknown>,
  filePath: string
): Record<string, unknown> {
  if (raw.slug && raw.track_code && raw.level) {
    return { ...raw };
  }

  const base = path.basename(filePath, '.json');
  const recipeId = (raw.recipe_id as string) || base;
  const track = mapTrackCode(String(raw.track || ''));
  const level = mapLevel(String(raw.tier || raw.difficulty || ''));
  const slug = `och-${track}-${String(recipeId).toLowerCase()}-${level}`;
  const title = (raw.title as string) || recipeId;
  const stepsIn = Array.isArray(raw.steps) ? (raw.steps as Record<string, unknown>[]) : [];
  const steps = stepsIn.map((st, i) => ({
    step_number: typeof st.number === 'number' ? st.number : i + 1,
    instruction: String(
      st.instruction || `${st.title || 'Step'}: ${st.description || ''}`
    ).trim(),
    expected_outcome: String(st.expected_output || st.tip || st.description || ''),
    evidence_hint: typeof st.tip === 'string' ? st.tip : undefined,
  }));

  const prerequisites = Array.isArray(raw.prerequisites) ? (raw.prerequisites as string[]) : [];
  const tools = Array.isArray(raw.tools_required) ? (raw.tools_required as string[]) : [];

  return {
    slug,
    title,
    track_code: track,
    skill_code: String(raw.pillar || 'general')
      .toLowerCase()
      .replace(/\s+/g, '_')
      .replace(/[^a-z0-9_]/g, '')
      .slice(0, 64),
    level,
    source_type: 'och_bundle',
    description: String(raw.when_to_use || title),
    prerequisites,
    tools_and_environment: tools.length ? tools : prerequisites.slice(0, 5),
    inputs: [],
    steps,
    validation_checks: [],
    expected_duration_minutes: parseEstimatedMinutes(raw.estimated_time as string | undefined),
    linked_missions: Array.isArray(raw.linked_missions) ? raw.linked_missions : [],
    created_at: new Date().toISOString(),
  };
}

/** Load every recipe JSON under `data/recipes`, OCH subfolders included. First file wins on slug collision. */
export function loadAllRecipesNormalized(cwd: string): Record<string, unknown>[] {
  const recipesDir = path.join(cwd, 'data', 'recipes');
  const files = walkRecipeJsonFiles(recipesDir);
  files.sort((a, b) => {
    const ao = a.includes(`${path.sep}och${path.sep}`) ? 1 : 0;
    const bo = b.includes(`${path.sep}och${path.sep}`) ? 1 : 0;
    return ao - bo;
  });

  const bySlug = new Map<string, Record<string, unknown>>();
  for (const f of files) {
    try {
      const raw = JSON.parse(fs.readFileSync(f, 'utf-8')) as Record<string, unknown>;
      const n = normalizeRecipeJson(raw, f);
      const slug = n.slug as string;
      if (!bySlug.has(slug)) bySlug.set(slug, n);
    } catch (e) {
      console.error(`Error parsing ${f}:`, e);
    }
  }
  return Array.from(bySlug.values());
}

/** Resolve a single recipe by slug (canonical or OCH-normalized). */
export function findRecipeNormalizedBySlug(
  cwd: string,
  slug: string
): Record<string, unknown> | null {
  const recipesDir = path.join(cwd, 'data', 'recipes');
  const files = walkRecipeJsonFiles(recipesDir);
  files.sort((a, b) => {
    const ao = a.includes(`${path.sep}och${path.sep}`) ? 1 : 0;
    const bo = b.includes(`${path.sep}och${path.sep}`) ? 1 : 0;
    return ao - bo;
  });
  for (const f of files) {
    try {
      const raw = JSON.parse(fs.readFileSync(f, 'utf-8')) as Record<string, unknown>;
      const n = normalizeRecipeJson(raw, f);
      if ((n.slug as string) === slug) return n;
    } catch {
      continue;
    }
  }
  return null;
}

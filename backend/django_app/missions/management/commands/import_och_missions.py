"""
Import OCH mission JSON from frontend/nextjs_app/data/missions/och/{beginner,intermediate,advanced,mastery}/

Uses raw SQL upserts against the **deployed** missions table (legacy columns: type, estimated_duration_minutes,
varchar difficulty) so imports work even when Mission ORM fields are ahead of the database.

Usage (from backend/django_app):
  python manage.py import_och_missions
  python manage.py import_och_missions --dry-run
"""

import json
import re
import uuid
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand
from django.db import connection, transaction

TRACK_ALIASES = {
    'offensive': 'offensive',
    'defender': 'defender',
    'defensive': 'defender',
    'grc': 'grc',
    'innovation': 'innovation',
    'leadership': 'leadership',
}


def _norm_track(raw: str | None) -> str:
    if not raw:
        return 'offensive'
    k = raw.strip().lower()
    if k in ('defensive', 'cyber_defense'):
        return 'defender'
    if k in TRACK_ALIASES:
        return TRACK_ALIASES[k]
    return k if k in ('defender', 'offensive', 'grc', 'innovation', 'leadership') else 'offensive'


def _norm_tier(raw: str | None) -> str:
    t = (raw or 'beginner').strip().lower()
    if t in ('beginner', 'intermediate', 'advanced', 'mastery'):
        return t
    return 'beginner'


def _difficulty_varchar(tier: str) -> str:
    """Legacy missions.difficulty is varchar: novice|beginner|intermediate|advanced|elite."""
    t = tier.lower()
    if t == 'mastery':
        return 'elite'
    if t in ('beginner', 'intermediate', 'advanced'):
        return t
    return 'beginner'


def _type_varchar(code: str | None, tier: str) -> str:
    """Legacy missions.type is lab|scenario|project|capstone."""
    if code and 'CAP' in str(code).upper():
        return 'capstone'
    t = tier.lower()
    if t == 'beginner':
        return 'lab'
    if t == 'intermediate':
        return 'scenario'
    if t in ('advanced', 'mastery'):
        return 'project'
    return 'scenario'


def _parse_estimated_minutes(val: Any) -> int:
    if val is None:
        return 120
    s = str(val).lower().strip()
    m = re.search(r'(\d+)\s*-\s*(\d+)\s*min', s)
    if m:
        return (int(m.group(1)) + int(m.group(2))) // 2
    m = re.search(r'(\d+)\s*min', s)
    if m:
        return int(m.group(1))
    m = re.search(r'(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*hrs?', s)
    if m:
        return int(round((float(m.group(1)) + float(m.group(2))) / 2 * 60))
    m = re.search(r'(\d+(?:\.\d+)?)\s*hrs?', s)
    if m:
        return int(round(float(m.group(1)) * 60))
    return 120


def _normalize_subtasks(raw_list: Any):
    out = []
    for st in raw_list or []:
        if not isinstance(st, dict):
            continue
        num = st.get('number') or len(out) + 1
        out.append({
            'id': num,
            'title': st.get('title') or f'Step {num}',
            'description': st.get('description') or '',
            'order_index': num,
            'evidence_required': st.get('evidence_required'),
            'detailed_guidance': st.get('detailed_guidance'),
        })
    return out


UPSERT_SQL = """
INSERT INTO missions (
    id, code, title, description, story, objectives, subtasks,
    track, tier, difficulty, type, track_id, track_key,
    estimated_duration_minutes, requires_mentor_review,
    recipe_recommendations, success_criteria, competencies,
    requirements, is_active, templates, ideal_path,
    presentation_required, escalation_events, environmental_cues,
    module_id, created_at
) VALUES (
    %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb,
    %s, %s, %s, %s, NULL, %s,
    %s, %s,
    %s::jsonb, '{}'::jsonb, %s::jsonb,
    '{}'::jsonb, %s, '[]'::jsonb, '{}'::jsonb,
    %s, '[]'::jsonb, '[]'::jsonb,
    NULL, NOW()
)
ON CONFLICT (code) DO UPDATE SET
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    story = EXCLUDED.story,
    objectives = EXCLUDED.objectives,
    subtasks = EXCLUDED.subtasks,
    track = EXCLUDED.track,
    tier = EXCLUDED.tier,
    difficulty = EXCLUDED.difficulty,
    type = EXCLUDED.type,
    track_key = EXCLUDED.track_key,
    estimated_duration_minutes = EXCLUDED.estimated_duration_minutes,
    recipe_recommendations = EXCLUDED.recipe_recommendations,
    competencies = EXCLUDED.competencies,
    is_active = EXCLUDED.is_active,
    presentation_required = EXCLUDED.presentation_required
"""


def _upsert_postgres(params: tuple) -> None:
    with connection.cursor() as cursor:
        cursor.execute(UPSERT_SQL, params)


class Command(BaseCommand):
    help = 'Import OCH mission JSON files into missions table (track + tier; idempotent on code).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Parse and report without writing to the database',
        )

    def handle(self, *args, **options):
        dry_run: bool = options['dry_run']

        if connection.vendor != 'postgresql':
            self.stdout.write(
                self.style.ERROR(
                    'import_och_missions currently supports PostgreSQL only (legacy missions columns).'
                )
            )
            return

        repo_root = Path(__file__).resolve().parents[5]
        och_root = repo_root / 'frontend' / 'nextjs_app' / 'data' / 'missions' / 'och'

        if not och_root.is_dir():
            self.stdout.write(self.style.ERROR(f'OCH missions directory not found: {och_root}'))
            return

        level_dirs = ['beginner', 'intermediate', 'advanced', 'mastery']
        files = []
        for lev in level_dirs:
            d = och_root / lev
            if not d.is_dir():
                continue
            for p in sorted(d.glob('*.json')):
                if p.name == '_index.json':
                    continue
                files.append(p)

        if not files:
            self.stdout.write(self.style.WARNING(f'No mission JSON files under {och_root}'))
            return

        self.stdout.write(self.style.SUCCESS(f'Found {len(files)} OCH mission files'))

        upserted = 0
        errors = 0

        for path in files:
            try:
                with open(path, encoding='utf-8') as f:
                    data = json.load(f)

                code = (data.get('mission_id') or path.stem)[:50]
                title = (data.get('title') or code)[:255]
                tier = _norm_tier(data.get('tier'))
                track = _norm_track(data.get('track'))

                description = (data.get('scenario') or data.get('description') or title)[:8000]
                story = (data.get('scenario') or '')[:20000]
                objectives = data.get('learning_objectives') or []
                if not isinstance(objectives, list):
                    objectives = []

                competencies: list = []
                for key in ('key_topics', 'competencies'):
                    v = data.get(key)
                    if isinstance(v, list):
                        competencies.extend([str(x) for x in v])

                subtasks = _normalize_subtasks(data.get('subtasks'))
                est = max(1, _parse_estimated_minutes(data.get('estimated_time')))

                linked = data.get('linked_recipes') or []
                recipe_recommendations = [str(x) for x in linked] if isinstance(linked, list) else []

                diff_s = _difficulty_varchar(tier)
                type_s = _type_varchar(code, tier)
                pres = bool(data.get('presentation_required')) or tier == 'mastery'

                if dry_run:
                    self.stdout.write(f'  [dry-run] {code} -> track={track} tier={tier} type={type_s}')
                    upserted += 1
                    continue

                params = (
                    str(uuid.uuid4()),
                    code,
                    title,
                    description,
                    story,
                    json.dumps(objectives),
                    json.dumps(subtasks),
                    track,
                    tier,
                    diff_s,
                    type_s,
                    track,
                    est,
                    False,
                    json.dumps(recipe_recommendations),
                    json.dumps(competencies) if competencies else '[]',
                    True,
                    pres,
                )

                with transaction.atomic():
                    _upsert_postgres(params)

                upserted += 1
                self.stdout.write(self.style.SUCCESS(f'  Upserted: {code}'))

            except Exception as e:
                errors += 1
                self.stdout.write(self.style.ERROR(f'  Error {path.name}: {e}'))

        self.stdout.write('\n' + '=' * 50)
        if dry_run:
            self.stdout.write(self.style.SUCCESS(f'DRY RUN — would upsert {upserted} missions'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Done: upserted={upserted}, errors={errors}'))

        if not dry_run and errors == 0:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT code, COUNT(*) AS c FROM missions
                    WHERE code IS NOT NULL AND code != ''
                    GROUP BY code HAVING COUNT(*) > 1
                    """
                )
                dups = cursor.fetchall()
            if dups:
                self.stdout.write(self.style.ERROR(f'Duplicate codes in DB: {dups}'))
            else:
                self.stdout.write(self.style.SUCCESS('No duplicate mission codes (unique constraint OK).'))

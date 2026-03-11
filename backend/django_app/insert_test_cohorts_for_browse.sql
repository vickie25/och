-- Insert Test Cohorts for Browsing
-- Run this SQL to add sample cohorts that will appear on /cohorts/browse

-- First, let's check if we have programs and tracks
-- If not, create basic ones

-- Insert test program if it doesn't exist
INSERT INTO programs (id, name, category, description, duration_months, default_price, currency, status, created_at, updated_at)
VALUES (
    gen_random_uuid(),
    'Cybersecurity Professional Program',
    'technical',
    'Comprehensive cybersecurity training program with hands-on labs and real-world projects',
    6,
    100.00,
    'USD',
    'active',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
) ON CONFLICT (name) DO NOTHING;

-- Get the program ID
DO $$
DECLARE
    program_id UUID;
    defender_track_id UUID;
    offensive_track_id UUID;
    grc_track_id UUID;
BEGIN
    -- Get program ID
    SELECT id INTO program_id FROM programs WHERE name = 'Cybersecurity Professional Program' LIMIT 1;
    
    -- Insert tracks if they don't exist
    INSERT INTO tracks (id, program_id, name, key, description, created_at, updated_at)
    VALUES 
        (gen_random_uuid(), program_id, 'Cyber Defense', 'defender', 'Learn defensive cybersecurity techniques', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        (gen_random_uuid(), program_id, 'Offensive Security', 'offensive', 'Learn ethical hacking and penetration testing', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        (gen_random_uuid(), program_id, 'Governance Risk Compliance', 'grc', 'Learn cybersecurity governance and compliance', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    ON CONFLICT (program_id, key) DO NOTHING;
    
    -- Get track IDs
    SELECT id INTO defender_track_id FROM tracks WHERE key = 'defender' AND program_id = program_id LIMIT 1;
    SELECT id INTO offensive_track_id FROM tracks WHERE key = 'offensive' AND program_id = program_id LIMIT 1;
    SELECT id INTO grc_track_id FROM tracks WHERE key = 'grc' AND program_id = program_id LIMIT 1;
    
    -- Insert test cohorts
    INSERT INTO cohorts (
        id, 
        track_id, 
        name, 
        start_date, 
        end_date, 
        mode, 
        seat_cap, 
        mentor_ratio, 
        status, 
        published_to_homepage,
        enrollment_fee,
        payment_deadline_hours,
        created_at, 
        updated_at
    ) VALUES 
    (
        gen_random_uuid(),
        defender_track_id,
        'Cyber Defense Bootcamp - Spring 2024',
        CURRENT_DATE + INTERVAL '30 days',
        CURRENT_DATE + INTERVAL '120 days',
        'virtual',
        50,
        0.1,
        'active',
        TRUE,
        150.00,
        48,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    ),
    (
        gen_random_uuid(),
        offensive_track_id,
        'Ethical Hacking Intensive - Q2 2024',
        CURRENT_DATE + INTERVAL '45 days',
        CURRENT_DATE + INTERVAL '135 days',
        'hybrid',
        30,
        0.1,
        'active',
        TRUE,
        200.00,
        48,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    ),
    (
        gen_random_uuid(),
        grc_track_id,
        'GRC Fundamentals - Summer 2024',
        CURRENT_DATE + INTERVAL '60 days',
        CURRENT_DATE + INTERVAL '150 days',
        'onsite',
        25,
        0.1,
        'active',
        TRUE,
        175.00,
        48,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    ),
    (
        gen_random_uuid(),
        defender_track_id,
        'Advanced Cyber Defense - Fall 2024',
        CURRENT_DATE + INTERVAL '90 days',
        CURRENT_DATE + INTERVAL '180 days',
        'virtual',
        40,
        0.1,
        'active',
        TRUE,
        250.00,
        72,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    )
    ON CONFLICT (name) DO NOTHING;
    
END $$;

-- Verify cohorts were created
SELECT 
    c.name,
    c.start_date,
    c.end_date,
    c.mode,
    c.seat_cap,
    c.enrollment_fee,
    c.published_to_homepage,
    t.name as track_name
FROM cohorts c
LEFT JOIN tracks t ON c.track_id = t.id
WHERE c.published_to_homepage = TRUE
ORDER BY c.start_date;

-- Show count
SELECT COUNT(*) as published_cohorts_count 
FROM cohorts 
WHERE published_to_homepage = TRUE;
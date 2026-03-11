# 🗄️ Database Setup Guide - Cohort System

## Quick Start

Run this **ONE** SQL file to set up everything:

```bash
psql -U your_username -d your_database -f backend/django_app/COHORT_COMPLETE_MIGRATION.sql
```

That's it! This single file contains everything you need.

---

## What This Script Does

### ✅ Creates 8 New Tables

1. **cohort_day_materials** - Learning materials by day
2. **cohort_material_progress** - Student progress tracking
3. **cohort_exams** - Exam definitions
4. **cohort_exam_submissions** - Student exam submissions
5. **cohort_grades** - Comprehensive grades
6. **cohort_peer_messages** - Peer messaging
7. **cohort_mentor_messages** - Mentor messaging
8. **cohort_payments** - Payment tracking

### ✅ Updates Existing Tables

**cohort_public_applications**:
- ➕ Adds: `payment_deadline`, `onboarding_token`, `onboarding_link_sent_at`, `password_created_at`
- ➖ Removes: `interview_mentor_id`, `interview_score`, `interview_graded_at`, `interview_status`

**cohorts**:
- ➕ Adds: `enrollment_fee`, `payment_deadline_hours`

### ✅ Creates Indexes

- 8 indexes for performance optimization

### ✅ Creates Helper Functions

- `expire_overdue_payments()` - Auto-reject expired payments

---

## Step-by-Step Instructions

### Option 1: Using psql Command Line

```bash
# Navigate to your project
cd /path/to/och

# Run the migration
psql -U your_username -d your_database -f backend/django_app/COHORT_COMPLETE_MIGRATION.sql

# Example:
psql -U postgres -d ochdb -f backend/django_app/COHORT_COMPLETE_MIGRATION.sql
```

### Option 2: Using pgAdmin

1. Open pgAdmin
2. Connect to your database
3. Click **Tools** → **Query Tool**
4. Click **Open File** icon
5. Select `backend/django_app/COHORT_COMPLETE_MIGRATION.sql`
6. Click **Execute** (F5)

### Option 3: Using DBeaver

1. Open DBeaver
2. Connect to your database
3. Right-click database → **SQL Editor** → **Open SQL Script**
4. Select `backend/django_app/COHORT_COMPLETE_MIGRATION.sql`
5. Click **Execute SQL Script** (Ctrl+Enter)

### Option 4: Copy-Paste

1. Open the SQL file in a text editor
2. Copy all contents
3. Paste into your database query tool
4. Execute

---

## Verification

After running the script, verify everything was created:

### Check Tables Created

```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_name LIKE 'cohort%' 
ORDER BY table_name;
```

**Expected Output** (8 tables):
```
cohort_day_materials
cohort_exam_submissions
cohort_exams
cohort_grades
cohort_mentor_messages
cohort_payments
cohort_peer_messages
cohort_material_progress
```

### Check New Columns in Applications

```sql
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'cohort_public_applications' 
AND column_name IN ('payment_deadline', 'onboarding_token', 'onboarding_link_sent_at', 'password_created_at');
```

**Expected Output** (4 columns):
```
onboarding_link_sent_at | timestamp with time zone
onboarding_token        | character varying
password_created_at     | timestamp with time zone
payment_deadline        | timestamp with time zone
```

### Check New Columns in Cohorts

```sql
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'cohorts' 
AND column_name IN ('enrollment_fee', 'payment_deadline_hours');
```

**Expected Output** (2 columns):
```
enrollment_fee          | numeric
payment_deadline_hours  | integer
```

### Verify Interview Columns Removed

```sql
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'cohort_public_applications' 
AND column_name LIKE 'interview%';
```

**Expected Output**: 0 rows (all interview columns removed)

---

## Troubleshooting

### Error: "relation already exists"

**Cause**: Tables already exist from a previous run.

**Solution**: The script uses `IF NOT EXISTS`, so this is safe to ignore. Or drop tables first:

```sql
DROP TABLE IF EXISTS cohort_payments CASCADE;
DROP TABLE IF EXISTS cohort_mentor_messages CASCADE;
DROP TABLE IF EXISTS cohort_peer_messages CASCADE;
DROP TABLE IF EXISTS cohort_grades CASCADE;
DROP TABLE IF EXISTS cohort_exam_submissions CASCADE;
DROP TABLE IF EXISTS cohort_exams CASCADE;
DROP TABLE IF EXISTS cohort_material_progress CASCADE;
DROP TABLE IF EXISTS cohort_day_materials CASCADE;
```

### Error: "column already exists"

**Cause**: Columns already exist from a previous run.

**Solution**: The script uses `IF NOT EXISTS`, so this is safe to ignore.

### Error: "relation does not exist"

**Cause**: Referenced tables (cohorts, enrollments, users) don't exist yet.

**Solution**: Make sure you've run the main database migrations first:

```bash
python manage.py migrate
```

### Error: Permission denied

**Cause**: User doesn't have permission to create tables.

**Solution**: Run as superuser or grant permissions:

```sql
GRANT ALL PRIVILEGES ON DATABASE your_database TO your_username;
```

---

## Rollback (If Needed)

If you need to undo the changes:

```sql
-- Drop new tables
DROP TABLE IF EXISTS cohort_payments CASCADE;
DROP TABLE IF EXISTS cohort_mentor_messages CASCADE;
DROP TABLE IF EXISTS cohort_peer_messages CASCADE;
DROP TABLE IF EXISTS cohort_grades CASCADE;
DROP TABLE IF EXISTS cohort_exam_submissions CASCADE;
DROP TABLE IF EXISTS cohort_exams CASCADE;
DROP TABLE IF EXISTS cohort_material_progress CASCADE;
DROP TABLE IF EXISTS cohort_day_materials CASCADE;

-- Remove new columns from cohort_public_applications
ALTER TABLE cohort_public_applications
DROP COLUMN IF EXISTS payment_deadline,
DROP COLUMN IF EXISTS onboarding_link_sent_at,
DROP COLUMN IF EXISTS password_created_at,
DROP COLUMN IF EXISTS onboarding_token;

-- Remove new columns from cohorts
ALTER TABLE cohorts
DROP COLUMN IF EXISTS enrollment_fee,
DROP COLUMN IF EXISTS payment_deadline_hours;

-- Drop function
DROP FUNCTION IF EXISTS expire_overdue_payments();
```

---

## What's Next?

After running the SQL migration:

1. ✅ **Update Django Settings**
   ```python
   # settings.py
   INSTALLED_APPS = [
       ...
       'cohorts',
       ...
   ]
   ```

2. ✅ **Update URLs**
   ```python
   # urls.py
   path('api/v1/cohorts/', include('cohorts.urls')),
   ```

3. ✅ **Set Environment Variables**
   ```bash
   export PAYSTACK_SECRET_KEY=sk_live_xxxxx
   export PAYSTACK_PUBLIC_KEY=pk_live_xxxxx
   export FRONTEND_URL=https://yourapp.com
   ```

4. ✅ **Restart Django**
   ```bash
   python manage.py collectstatic
   systemctl restart gunicorn
   ```

5. ✅ **Deploy Frontend**
   ```bash
   cd frontend/nextjs_app
   npm run build
   npm start
   ```

6. ✅ **Test the Flow**
   - Create test cohort
   - Submit application
   - Auto-grade applications
   - Create account
   - Complete payment
   - Verify enrollment

---

## Summary

**Single Command**:
```bash
psql -U your_username -d your_database -f backend/django_app/COHORT_COMPLETE_MIGRATION.sql
```

**What It Does**:
- Creates 8 new tables
- Updates 2 existing tables
- Creates 8 indexes
- Creates 1 helper function
- Adds documentation

**Time**: ~5 seconds

**Safe**: Uses `IF NOT EXISTS` - won't break existing data

---

## Need Help?

- **Check logs**: Look for error messages in psql output
- **Verify connection**: Make sure you can connect to the database
- **Check permissions**: Ensure user has CREATE TABLE privileges
- **Review script**: Open the SQL file to see what it does

---

**Ready to run? Execute the command above! 🚀**

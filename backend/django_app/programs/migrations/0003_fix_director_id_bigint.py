from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('programs', '0002_initial'),
        ('users', '0001_initial'),
    ]

    operations = [
        # Remove the old foreign key constraint if it exists
        migrations.RunSQL(
            "ALTER TABLE tracks DROP CONSTRAINT IF EXISTS tracks_director_id_fkey;",
            reverse_sql="-- No reverse needed"
        ),
        
        # Ensure the column type is BIGINT (to match BigInt User IDs)
        migrations.RunSQL(
            "ALTER TABLE tracks ALTER COLUMN director_id TYPE BIGINT USING director_id::bigint;",
            reverse_sql="-- Reversing might be complex, typically leave as bigint"
        ),
        
        # Add the foreign key back with correct reference to BigInt Users
        migrations.RunSQL(
            "ALTER TABLE tracks ADD CONSTRAINT tracks_director_id_fkey FOREIGN KEY (director_id) REFERENCES users(id) ON DELETE SET NULL;",
            reverse_sql="ALTER TABLE tracks DROP CONSTRAINT IF EXISTS tracks_director_id_fkey;"
        ),
    ]
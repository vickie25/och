# Generated manually to fix: column curriculum_tracks.slug does not exist
# Simplified to avoid Django's duplicate index bug on AlterField for SlugFields

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('curriculum', '0007_tier3_completion_config'),
    ]

    operations = [
        migrations.AddField(
            model_name='curriculumtrack',
            name='slug',
            field=models.SlugField(help_text="'defender', 'offensive', 'grc', 'innovation', 'leadership'", max_length=50, null=True, unique=False, db_index=False),
        ),
        migrations.AddField(
            model_name='curriculumtrack',
            name='title',
            field=models.CharField(default='', help_text='Display title', max_length=255),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='curriculumtrack',
            name='order_number',
            field=models.IntegerField(default=1, help_text='Display order'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='curriculumtrack',
            name='thumbnail_url',
            field=models.URLField(blank=True, default='', help_text='Track thumbnail image'),
            preserve_default=True,
        ),
    ]

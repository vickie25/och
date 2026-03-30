# Generated manually on 2026-03-29
# Adds MentorRating, MentorCredit, CreditTransaction, CreditRedemption models
# and average_rating field to Mentor model

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mentors', '0001_create_mentor_models'),
    ]

    operations = [
        # Add average_rating field to Mentor model
        migrations.AddField(
            model_name='mentor',
            name='average_rating',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='Average rating from all student ratings (1-5)',
                max_digits=3,
                null=True
            ),
        ),
        
        # Create MentorRating model
        migrations.CreateModel(
            name='MentorRating',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('rating', models.IntegerField(choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)], help_text='Rating from 1-5 stars')),
                ('review', models.TextField(blank=True, null=True, help_text='Written review/feedback')),
                ('credits_awarded', models.IntegerField(default=0, help_text='Credits awarded to mentor based on rating')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('mentor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ratings', to='mentors.mentor')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mentor_ratings_given', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'mentor_ratings',
                'ordering': ['-created_at'],
            },
        ),
        
        # Create MentorCredit model
        migrations.CreateModel(
            name='MentorCredit',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('total_earned', models.IntegerField(default=0, help_text='Total credits ever earned')),
                ('total_redeemed', models.IntegerField(default=0, help_text='Total credits redeemed')),
                ('current_balance', models.IntegerField(default=0, help_text='Available credits')),
                ('last_earned_at', models.DateTimeField(blank=True, null=True)),
                ('last_redeemed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('mentor', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='credit_balance', to='mentors.mentor')),
            ],
            options={
                'db_table': 'mentor_credits',
                'ordering': ['-current_balance'],
            },
        ),
        
        # Create CreditTransaction model
        migrations.CreateModel(
            name='CreditTransaction',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('transaction_type', models.CharField(choices=[('earned', 'Credits Earned'), ('redeemed', 'Credits Redeemed'), ('expired', 'Credits Expired')], max_length=20)),
                ('amount', models.IntegerField(help_text='Number of credits')),
                ('description', models.CharField(max_length=255)),
                ('source', models.CharField(blank=True, choices=[('rating', 'Student Rating'), ('bonus', 'Platform Bonus'), ('referral', 'Referral'), ('achievement', 'Achievement Unlock')], max_length=50, null=True)),
                ('balance_after', models.IntegerField(help_text='Balance after this transaction')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('mentor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='credit_transactions', to='mentors.mentor')),
                ('related_rating', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='credit_transaction', to='mentors.mentorrating')),
            ],
            options={
                'db_table': 'credit_transactions',
                'ordering': ['-created_at'],
            },
        ),
        
        # Create CreditRedemption model
        migrations.CreateModel(
            name='CreditRedemption',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('redemption_type', models.CharField(choices=[('course', 'Course Purchase'), ('certificate', 'Certificate Generation'), ('badge', 'Profile Badge'), ('priority_matching', 'Priority Student Matching'), ('featured_profile', 'Featured Profile')], max_length=30)),
                ('credits_used', models.IntegerField(help_text='Credits redeemed')),
                ('description', models.CharField(help_text='What was redeemed', max_length=255)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], default='pending', max_length=20)),
                ('course_id', models.UUIDField(blank=True, help_text='If redeeming for course', null=True)),
                ('certificate_id', models.UUIDField(blank=True, help_text='If generating certificate', null=True)),
                ('badge_type', models.CharField(blank=True, help_text='If redeeming for badge', max_length=50, null=True)),
                ('redeemed_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('mentor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='credit_redemptions', to='mentors.mentor')),
            ],
            options={
                'db_table': 'credit_redemptions',
                'ordering': ['-redeemed_at'],
            },
        ),
        
        # Add unique constraint on MentorRating (one rating per student per mentor)
        migrations.AlterUniqueTogether(
            name='mentorrating',
            unique_together={('mentor', 'student')},
        ),
        
        # Add indexes
        migrations.AddIndex(
            model_name='mentorrating',
            index=models.Index(fields=['mentor', 'rating'], name='mentor_rate_mentor_r_1f8c2e_idx'),
        ),
        migrations.AddIndex(
            model_name='mentorrating',
            index=models.Index(fields=['student'], name='mentor_rate_student_3f2a1b_idx'),
        ),
        migrations.AddIndex(
            model_name='credittransaction',
            index=models.Index(fields=['mentor', 'created_at'], name='credit_trans_mentor_c_8d4e5f_idx'),
        ),
        migrations.AddIndex(
            model_name='creditredemption',
            index=models.Index(fields=['mentor', 'status'], name='credit_redem_mentor_s_9a7b6c_idx'),
        ),
    ]

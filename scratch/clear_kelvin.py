import os
import django
import sys

# Set up Django environment
sys.path.append('/var/www/och/backend/django_app')
# Make sure we use the current dir if running inside docker
# Actually if we run this via docker-compose exec it mounts to /app
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
django.setup()

from django.contrib.auth import get_user_model
from coaching.models import (
    AICoachSession, AICoachMessage, Habit, HabitLog, Goal, Reflection, StudentAnalytics
)
from profiler.models import ProfilerSession, ProfilerResult

User = get_user_model()

def clear_kelvin_progress():
    print("--- 🧹 Clearing Kelvin Progress ---")
    user = User.objects.filter(email='kelvin202maina@gmail.com').first()
    
    if not user:
        print("User kelvin202maina@gmail.com not found!")
        return

    print(f"Found user: {user.email} (ID: {user.id})")

    # 1. Clear AI Coaching Data
    AICoachMessage.objects.filter(session__user=user).delete()
    AICoachSession.objects.filter(user=user).delete()
    print("✅ Cleared AI Coaching sessions")

    # 2. Clear Coaching OS Data
    HabitLog.objects.filter(user=user).delete()
    Habit.objects.filter(user=user).delete()
    Goal.objects.filter(user=user).delete()
    Reflection.objects.filter(user=user).delete()
    print("✅ Cleared Coaching OS Data (Habits, Goals, Reflections)")

    # 3. Clear Profiler Data
    ProfilerResult.objects.filter(user=user).delete()
    ProfilerSession.objects.filter(user=user).delete()
    print("✅ Cleared Profiler Data")

    # 4. Initialize Fresh Analytics (The "New Plan")
    StudentAnalytics.objects.filter(user=user).delete()
    analytics = StudentAnalytics.objects.create(
        user=user,
        total_missions_completed=0,
        average_score=0,
        recipes_completed=0,
        current_streak=0,
        weak_areas=[],
        next_goals=[]
    )
    print("✅ Initialized fresh StudentAnalytics")

    print("\n🎉 Kelvin's progress has been fully cleared. Ready for fresh testing when you return!")

if __name__ == "__main__":
    clear_kelvin_progress()

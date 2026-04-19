from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from programs.models import Program

User = get_user_model()

def run():
    client = APIClient()
    
    # Get or create a superuser/director to run the test
    user = User.objects.filter(is_superuser=True).first()
    if not user:
        user = User.objects.first()
        
    client.force_authenticate(user=user)
    
    print(f"Testing program creation as user: {user.email}")
    
    payload = {
        "name": "Test Cyber Program",
        "category": "technical",
        "categories": ["technical", "security"],
        "description": "Test description",
        "duration_months": 6,
        "default_price": 5000,
        "currency": "KSh",
        "outcomes": ["Understand testing"],
        "missions_registry_link": "https://example.com"
    }
    
    response = client.post('/api/v1/director/programs/', payload, format='json')
    print("Response Status Code:", response.status_code)
    print("Response Data:", response.data)
    
    if response.status_code == 201:
        print("SUCCESS! Program creation endpoint works.")
        # Cleanup
        Program.objects.filter(id=response.data['id']).delete()
    else:
        print("FAILED!")

run()

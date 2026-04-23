import os
import paramiko

def patch_ai_coach():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('69.30.235.220', username='administrator', password=os.environ.get('PRODUCTION_SSH_PASSWORD', ''))
    
    # Patch script to run inside container
    patch_script = """
import shutil
path = '/app/coaching/views.py'
shutil.copy(path, path + '.bak')

with open(path, 'r') as f:
    content = f.read()

# Fix 1: Ensure progress is NEVER None before .get()
content = content.replace(
    "progress = request.data.get('progress') or {}",
    "progress = request.data.get('progress'); progress = progress if isinstance(progress, dict) else {}"
)

# Fix 2: Safety check for track_info tuple
content = content.replace(
    "track_info, track_level, match_score = get_user_track_info(user)",
    "track_data = get_user_track_info(user); track_info, track_level, match_score = track_data if (track_data and len(track_data)==3) else ('General', 'BEGINNER', 0)"
)

# Fix 3: OpenAI response safety
old_resp = "ai_response = response.choices[0].message.content"
new_resp = \"\"\"
        if not response or not response.choices:
            raise Exception('AI response was empty')
        ai_response = response.choices[0].message.content
        if not ai_response:
            raise Exception('AI returned empty content')
\"\"\"
content = content.replace(old_resp, new_resp.strip())

with open(path, 'w') as f:
    f.write(content)
print('AI Coach view patched successfully with safety nets.')
"""
    client.exec_command(f"docker exec -i hub_prod_django python << 'EOF'\n{patch_script}\nEOF")
    client.close()

if __name__ == "__main__":
    patch_ai_coach()

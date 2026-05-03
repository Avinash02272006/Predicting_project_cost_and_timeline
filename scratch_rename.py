import sys

def process():
    with open('app.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    in_chat = False
    for i, line in enumerate(lines):
        if 'def chat():' in line:
            in_chat = True
        elif 'def clear():' in line:
            in_chat = False
            
        if in_chat:
            if "session = project_sessions" in line:
                lines[i] = line.replace("session = project_sessions", "proj_session = project_sessions")
            elif "session.get" in line and "'user_id' not in session" not in line:
                lines[i] = line.replace("session.get", "proj_session.get")
            elif "session[\"" in line:
                lines[i] = line.replace("session[\"", "proj_session[\"")
            elif "session['" in line and "'user_id' not in session" not in line:
                lines[i] = line.replace("session['", "proj_session['")
            
    with open('app.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)

process()

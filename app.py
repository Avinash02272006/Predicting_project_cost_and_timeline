from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from flask_cors import CORS
import joblib
import numpy as np
import os

print("Starting app...")
app = Flask(__name__)
app.secret_key = "super_secret_key_for_ai_predictor"
CORS(app)

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL)''')
    conn.commit()
    conn.close()

init_db()

# Load trained model
print("Loading model...")
model_path = os.path.join("models", "project_model.joblib")
model = joblib.load(model_path)
print("Model loaded.")

# Temporary session-like storage (for simplicity)
project_sessions = {}

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if not username or not password:
            return render_template("register.html", error="Please provide username and password.")
        
        hashed_pw = generate_password_hash(password)
        try:
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_pw))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return render_template("register.html", error="Username already exists.")
            
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()
        
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect(url_for('home'))
        else:
            return render_template("login.html", error="Invalid username or password.")
            
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route("/")
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template("index.html", username=session.get('username'))

@app.route("/chat", methods=["POST"])
def chat():
    if 'user_id' not in session:
        return jsonify({"reply": "⚠️ Please log in to use the AI chatbot.", "chart_data": {}})
    try:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            return jsonify({"reply": "⚠️ Please set your GROQ_API_KEY environment variable to use the AI chatbot.", "chart_data": {}})

        from groq import Groq
        client = Groq(api_key=api_key)

        data = request.get_json()
        user_id = data.get("user_id", "default")
        message = data.get("message", "").strip()

        # Initialize session if not exists
        if user_id not in project_sessions:
            project_sessions[user_id] = {
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a friendly AI Project Estimator Assistant. Your goal is to gather the following 6 pieces of information from the user about their software project:\n1. Description of the project\n2. Number of developers (Team Size) - MUST be an integer\n3. Number of core features (Features) - MUST be an integer\n4. Target Platforms (e.g., Web, iOS, Android)\n5. Expected User Traffic (e.g., Low, Medium, High)\n6. Timeline Urgency (e.g., Flexible, Strict, Rush)\n\nConverse naturally with the user to get this info. Ask one or two questions at a time. Do not overwhelm them. Acknowledge their inputs nicely.\n\nCRITICAL INSTRUCTION: Once you have gathered ALL 6 pieces of information, you MUST output a raw JSON block with EXACTLY this structure and NOTHING else (no conversational text before or after):\n{\n  \"description\": \"...\",\n  \"team_size\": 2,\n  \"features\": 5,\n  \"platforms\": \"...\",\n  \"traffic\": \"...\",\n  \"urgency\": \"...\"\n}\nDo not output JSON until you have all the info."
                    }
                ],
                "is_complete": False,
                "complexity": None
            }

        proj_session = project_sessions[user_id]

        if proj_session.get("is_complete"):
            return jsonify({"reply": "We already generated your report! Click 'Start Over' to create a new one.", "chart_data": {}})

        if proj_session["messages"] and proj_session["messages"][-1]["role"] == "user":
            proj_session["messages"][-1]["content"] += "\n" + message
        else:
            proj_session["messages"].append({"role": "user", "content": message})

        # Call Groq API
        try:
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=proj_session["messages"],
                temperature=0.5
            )
            ai_reply = response.choices[0].message.content.strip()
        except Exception as e:
            print("Groq API Error:", e)
            return jsonify({"reply": "⚠️ Error communicating with Groq API.", "chart_data": {}})

        import json
        import re

        is_json_complete = False
        parsed = None

        # Extract JSON if the LLM wrapped it in text
        json_match = re.search(r'\{[\s\S]*\}', ai_reply)
        if json_match:
            try:
                parsed = json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        if parsed and isinstance(parsed, dict) and all(k in parsed for k in ["description", "team_size", "features", "platforms", "traffic", "urgency"]):
            try:
                proj_session["description"] = str(parsed["description"])
                proj_session["team_size"] = int(parsed["team_size"])
                proj_session["features"] = int(parsed["features"])
                proj_session["platforms"] = str(parsed["platforms"])
                proj_session["traffic"] = str(parsed["traffic"])
                proj_session["urgency"] = str(parsed["urgency"])
                proj_session["is_complete"] = True
                is_json_complete = True
            except Exception:
                pass

        if not is_json_complete:
            proj_session["messages"].append({"role": "assistant", "content": ai_reply})
            return jsonify({"reply": ai_reply, "chart_data": {}})

        # All info available, predict
        # Decide complexity based on description length + new features
        if proj_session.get("complexity") is None:
            complexity_score = 3
            desc = proj_session["description"].lower()
            if "complex" in desc or "ai" in desc or "machine learning" in desc or "enterprise" in desc:
                complexity_score += 1
            if "simple" in desc or "basic" in desc or "minimal" in desc:
                complexity_score -= 1
            
            traffic = proj_session["traffic"].lower()
            if "high" in traffic or "million" in traffic or "100k" in traffic:
                complexity_score += 1
                
            platforms = proj_session["platforms"].lower()
            if "ios" in platforms and "android" in platforms and "web" in platforms:
                complexity_score += 1
                
            proj_session["complexity"] = min(5, max(1, complexity_score))

        prediction = model.predict([[proj_session["complexity"], proj_session["team_size"], proj_session["features"]]])[0]
        estimated_cost = round(prediction[0], 2)
        estimated_timeline = round(prediction[1], 1)

        # Cost Modifiers based on Urgency
        urgency = proj_session["urgency"].lower()
        if "rush" in urgency or "strict" in urgency or "fast" in urgency or "urgent" in urgency:
            estimated_cost *= 1.25 # 25% rush fee
            estimated_timeline *= 0.75 # 25% faster
            
        traffic = proj_session["traffic"].lower()
        infrastructure_cost = 5000 # Base INR per month
        if "high" in traffic or "million" in traffic or "10k" in traffic:
            infrastructure_cost = 25000
        elif "medium" in traffic:
            infrastructure_cost = 10000

        maintenance_cost = round(estimated_cost * 0.20, 2)

        # Let Groq generate the sophisticated analysis and SWOT based on ML outputs
        final_prompt = f"""
        You are an elite Software Architect and Business Analyst. The user wants to build: "{proj_session['description']}".
        Target Platforms: {proj_session['platforms']} | Expected Traffic: {proj_session['traffic']} | Urgency: {proj_session['urgency']}
        Team Size: {proj_session['team_size']} | Core Features: {proj_session['features']}
        
        Our internal Machine Learning model has predicted the following baseline metrics:
        - Initial Development Cost: ₹{estimated_cost:,.2f}
        - Estimated Timeline: {estimated_timeline:.1f} weeks
        - Annual Maintenance: ₹{maintenance_cost:,.2f}
        - Monthly Infrastructure: ₹{infrastructure_cost:,.2f}

        Write a gorgeous, professional, highly detailed Executive Report in Markdown format. It MUST include the following sections exactly:
        
        ### 🚀 Executive Summary
        (A brief, highly personalized overview of the project's viability and market positioning. 2-3 sentences max.)

        ### 💰 Financial & Timeline Breakdown
        (Display the exact metrics provided above cleanly using bullet points.)

        ### 🛠 Recommended Technical Strategy
        (Crisp bullet points of the tech stack, architecture, and team roles.)

        ### 📊 SWOT Analysis
        (Strengths, Weaknesses, Opportunities, Threats specific to their idea. Use short, punchy bullet points.)

        ### 🎯 Actionable Next Steps
        (3 to 5 immediate, practical bullet points to get started.)
        
        CRITICAL PERSONA RULES:
        - Do NOT sound like ChatGPT. Never use phrases like "We are excited to present", "In conclusion", or "Here is an analysis".
        - Use a brutally minimalist, data-driven, hyper-analytical tone (like an elite Silicon Valley quantitative consultant).
        - Drop all pleasantries. Start immediately with the data. 
        - Keep all paragraphs extremely short, crisp, and concise.
        - Use punchy, highly readable business language.
        - Use rich Markdown styling (bolding, lists). 
        - Do NOT output any JSON. Just the beautifully formatted Markdown report.
        """
        
        try:
            report_response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": final_prompt}],
                temperature=0.7
            )
            reply = report_response.choices[0].message.content.strip()
        except Exception as e:
            print("Groq Report Gen Error:", e)
            reply = f"Error generating advanced AI report. Fallback ML stats: Cost ₹{estimated_cost:,.2f}, Time {estimated_timeline:.1f} weeks."

        # Phases for timeline chart
        phase1_time = round(estimated_timeline * 0.2, 1)
        phase2_time = round(estimated_timeline * 0.5, 1)
        phase3_time = round(estimated_timeline * 0.2, 1)
        phase4_time = round(estimated_timeline * 0.1, 1)

        # Extra Chart Data Generation
        urgency = proj_session['urgency'].lower()
        traffic = proj_session['traffic'].lower()
        risk_tech = min(100, proj_session['features'] * 10)
        risk_market = 80 if "high" in traffic else 40
        risk_time = 90 if "rush" in urgency else 30
        risk_cost = min(100, int(estimated_cost / 1500))
        risk_team = 80 if proj_session['team_size'] < 3 else 30

        # Charts
        chart_data = {
            "cost_labels": ["Development (60%)", "Design (15%)", "QA & Testing (15%)", "Project Mgmt (10%)"],
            "cost_values": [
                estimated_cost * 0.6,
                estimated_cost * 0.15,
                estimated_cost * 0.15,
                estimated_cost * 0.1,
            ],
            "time_labels": ["Design & Planning", "Development", "Testing", "Deployment"],
            "time_values": [
                phase1_time,
                phase2_time,
                phase3_time,
                phase4_time,
            ],
            "radar_labels": ["Tech Risk", "Market Risk", "Time Crunch", "Budget Strain", "Team Load"],
            "radar_values": [risk_tech, risk_market, risk_time, risk_cost, risk_team],
            "line_labels": ["M1", "M2", "M3", "M4", "M5", "M6"],
            "line_values": [
                infrastructure_cost * 1.0,
                infrastructure_cost * 1.5,
                infrastructure_cost * 2.2,
                infrastructure_cost * 3.5,
                infrastructure_cost * 5.0,
                infrastructure_cost * 7.5
            ]
        }

        # Clear session after answer
        project_sessions.pop(user_id)

        return jsonify({"reply": reply, "chart_data": chart_data})

    except Exception as e:
        print("Error:", e)
        return jsonify({"reply": "⚠️ Something went wrong.", "chart_data": {}})

@app.route("/clear", methods=["POST"])
def clear():
    data = request.get_json()
    user_id = data.get("user_id")
    if user_id in project_sessions:
        project_sessions.pop(user_id)
    return jsonify({"status": "cleared"})

if __name__ == "__main__":
    app.run(debug=True)

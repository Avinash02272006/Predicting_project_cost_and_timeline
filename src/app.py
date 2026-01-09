
import streamlit as st
import pandas as pd
import requests
import json
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- Configuration ---
st.set_page_config(page_title="ProPredict AI", page_icon="⚡", layout="wide", initial_sidebar_state="collapsed")

API_URL = "http://127.0.0.1:8000"

# --- Assets Injection ---
def load_assets():
    with open("src/assets/style.css") as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    with open("src/assets/script.js") as f:
        st.markdown(f'<script>{f.read()}</script>', unsafe_allow_html=True)

load_assets()

# --- State Management ---
if 'access_token' not in st.session_state: st.session_state.access_token = None
if 'username' not in st.session_state: st.session_state.username = None
if 'current_view' not in st.session_state: st.session_state.current_view = 'new_chat' # 'new_chat' or 'history_view'
if 'last_prediction' not in st.session_state: st.session_state.last_prediction = None
if 'last_input' not in st.session_state: st.session_state.last_input = None

# --- Helpers ---
def get_headers():
    return {"Authorization": f"Bearer {st.session_state.access_token}"}

def login_user(username, password):
    try:
        res = requests.post(f"{API_URL}/token", data={"username": username, "password": password})
        if res.status_code == 200:
            st.session_state.access_token = res.json()['access_token']
            st.session_state.username = username
            st.rerun()
        else: st.error("Invalid credentials")
    except: st.error("Server Offline")

def register_user(username, email, password):
    try:
        res = requests.post(f"{API_URL}/register", json={"username": username, "email": email, "password": password})
        if res.status_code == 201: st.success("Joined! Login now.")
        else: st.error(res.json().get('detail'))
    except: st.error("Server Offline")

# --- UI Components ---

def render_login():
    # Facebook-style Split Screen
    col_left, col_right = st.columns([1.5, 1])
    
    with col_left:
        st.markdown("""
        <div class='login-left'>
            <div class='login-title'>ProPredict AI ⚡</div>
            <div class='login-subtitle'>
                The Future of IT Project Analytics.<br>
                Predict Timelines. Optimize Costs. <br>
                <b>Build Better Software.</b>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_right:
        st.markdown("<div class='login-card'>", unsafe_allow_html=True)
        tab_login, tab_reg = st.tabs(["Login", "Sign Up"])
        
        with tab_login:
            with st.form("login_f"):
                u = st.text_input("Username", placeholder="Enter username")
                p = st.text_input("Password", type="password", placeholder="••••••")
                if st.form_submit_button("Log In", use_container_width=True):
                    login_user(u, p)
        
        with tab_reg:
            with st.form("reg_f"):
                u = st.text_input("Username")
                e = st.text_input("Email")
                p = st.text_input("Password", type="password")
                if st.form_submit_button("Sign Up", use_container_width=True):
                    register_user(u, e, p)
        st.markdown("</div>", unsafe_allow_html=True)

def render_sidebar():
    with st.sidebar:
        st.title("ProPredict")
        if st.button("+ New Chat", use_container_width=True):
            st.session_state.current_view = 'new_chat'
            st.session_state.last_prediction = None
            st.rerun()
        
        st.divider()
        st.caption("History")
        
        # Fetch History
        try:
            h_res = requests.get(f"{API_URL}/history", headers=get_headers())
            if h_res.status_code == 200:
                history = h_res.json()
                for item in history:
                    label = f"{item['project_type']} ({item['timestamp'][:10]})"
                    if st.button(label, key=item['timestamp']):
                        st.session_state.current_view = 'history_view'
                        st.session_state.last_prediction = {
                            "predicted_delay_days": item['predicted_delay'],
                            "cost_overrun_percent": item['cost_overrun'],
                            "risk_level": "Historical",
                            "risk_color": "#888",
                            "confidence_score": 1.0
                        }
                        st.session_state.last_input = {
                            "project_description": item['project_description'],
                            "project_type": item['project_type']
                        }
                        st.rerun()
        except:
            st.warning("⚠️ Offline")
            
        st.markdown("---")
        if st.button("Log Out"):
            st.session_state.access_token = None
            st.rerun()

def render_main_chat():
    st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
    
    # 1. Input Section (New Chat) or History Display
    if st.session_state.current_view == 'new_chat' and not st.session_state.last_prediction:
        st.subheader("Start a New Analysis")
        with st.form("input_activator"):
            desc = st.text_area("Describe your project...", height=100, placeholder="e.g., A mobile app for food delivery using Flutter and Firebase...")
            
            c1, c2, c3 = st.columns(3)
            with c1: p_type = st.selectbox("Type", ['Web App', 'Mobile App', 'Enterprise', 'AI/ML', 'SaaS'])
            with c2: devs = st.number_input("Developers", 1, 50, 5)
            with c3: comp_manual = st.slider("Complexity", 1, 10, 5)

            # Hidden/Default fields for simplicity (User doesn't see ALL paramaters in chat mode usually)
            # using reasonable defaults or simplified inputs
            
            if st.form_submit_button("Analyze Project 🚀", use_container_width=True):
                # Calculate complexity proxy
                comp = min(10, comp_manual + (1 if "ai" in desc.lower() else 0))
                
                payload = {
                    "project_type": p_type,
                    "project_description": desc,
                    "complexity_score": comp,
                    "number_of_developers": devs,
                    "team_experience_rating": 3,
                    "dependency_delay_days": 5,
                    "resource_availability_ratio": 0.8,
                    "labour_cost_index": 1.5,
                    "historical_delay_days": 0
                }
                
                try:
                    with st.spinner("AI Computing..."):
                        r = requests.post(f"{API_URL}/predict", json=payload, headers=get_headers())
                        if r.status_code == 200:
                            st.session_state.last_prediction = r.json()
                            st.session_state.last_input = payload
                            st.rerun()
                        else:
                            st.error("Prediction Failed")
                except: st.error("Connection Failed")

    # 2. Results Display (Like a Chat Response)
    if st.session_state.last_prediction:
        # User Message
        user_in = st.session_state.last_input
        st.markdown(f"""
        <div class='user-msg'>
            <b>🧑‍💻 You:</b><br>
            {user_in.get('project_description', 'Project Analysis Request')}
            <br>
            <small>Type: {user_in.get('project_type')}</small>
        </div>
        """, unsafe_allow_html=True)
        
        # AI Response
        res = st.session_state.last_prediction
        st.markdown(f"""
        <div class='ai-msg'>
            <b>⚡ ProPredict AI:</b><br>
            Risk Assessment: <span style='color:{res['risk_color']}'><b>{res['risk_level']}</b></span>
        </div>
        """, unsafe_allow_html=True)
        
        # KPIs
        k1, k2, k3 = st.columns(3)
        with k1: 
            st.metric("Timeline Delay", f"{res['predicted_delay_days']} Days")
        with k2:
            st.metric("Cost Overrun", f"{res['cost_overrun_percent']}%")
        with k3:
            st.metric("Confidence", f"{int(res['confidence_score']*100)}%")
            
        st.divider()
        
        # Diagrammatic View (Visuals)
        st.caption("Visual Analysis")
        d1, d2 = st.columns(2)
        
        with d1:
            # Gauge Chart for Risk/Delay
            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = res['predicted_delay_days'],
                title = {'text': "Predicted Delay (Days)"},
                gauge = {'axis': {'range': [0, 100]}, 'bar': {'color': res['risk_color']}}
            ))
            fig.update_layout(height=250, margin=dict(l=20,r=20,t=50,b=20), paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"})
            st.plotly_chart(fig, use_container_width=True)
            
        with d2:
            # Bar chart for Cost
            fig2 = px.bar(x=['Budget', 'Overrun'], y=[100, res['cost_overrun_percent']], 
                         labels={'x': 'Metric', 'y': '%'}, title="Cost Analysis",
                         color=['Budget', 'Overrun'], color_discrete_sequence=['#4CAF50', res['risk_color']])
            fig2.update_layout(height=250, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font={'color': "white"})
            st.plotly_chart(fig2, use_container_width=True)

        # Suggestions
        try:
            sug_res = requests.post(f"{API_URL}/suggest", json=st.session_state.last_input, headers=get_headers())
            if sug_res.status_code == 200:
                sug = sug_res.json()
                st.info(f"💡 **Recommendation:** {sug['primary_suggestion']}")
        except: pass

        if st.button("New Analysis"):
            st.session_state.last_prediction = None
            st.session_state.current_view = 'new_chat'
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# --- Routing ---
if st.session_state.access_token:
    render_sidebar()
    render_main_chat()
else:
    render_login()

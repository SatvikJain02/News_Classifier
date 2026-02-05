# Command to run:
# streamlit run frontend.py

import streamlit as st
import requests

# 🔗 CONFIGURATION
# Ensure your FastAPI is running on this URL
API_URL = "https://news-classifier-2.onrender.com"

# 🛠️ HELPER FUNCTIONS
def login(username, password):
    try:
        response = requests.post(
            f"{API_URL}/login", 
            json={"username": username, "password": password}
        )
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except:
        return None

def register(username, password):
    try:
        response = requests.post(
            f"{API_URL}/register", 
            json={"username": username, "password": password}
        )
        return response.status_code == 200
    except:
        return False

def get_prediction(text, token):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"News Content": text} # Must match the 'alias' in your Pydantic model
    
    try:
        response = requests.post(f"{API_URL}/predict", json=payload, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": response.text}
    except Exception as e:
        return {"error": str(e)}

# 🖥️ UI LAYOUT

st.set_page_config(page_title="Truth Seeker AI", page_icon="🕵️‍♂️", layout="centered")

# Initialize Session State for Auth
if 'token' not in st.session_state:
    st.session_state.token = None
if 'username' not in st.session_state:
    st.session_state.username = None

# --- SIDEBAR (Login/Register) ---
with st.sidebar:
    st.header("🔐 Authentication")
    
    if st.session_state.token:
        st.success(f"Welcome, {st.session_state.username}!")
        if st.button("Logout"):
            st.session_state.token = None
            st.session_state.username = None
            st.rerun()
    else:
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:
            l_user = st.text_input("Username", key="l_user")
            l_pass = st.text_input("Password", type="password", key="l_pass")
            if st.button("Log In"):
                data = login(l_user, l_pass)
                if data:
                    st.session_state.token = data['access_token']
                    st.session_state.username = l_user
                    st.success("Logged in!")
                    st.rerun()
                else:
                    st.error("Invalid credentials or server down.")

        with tab2:
            r_user = st.text_input("New Username", key="r_user")
            r_pass = st.text_input("New Password", type="password", key="r_pass")
            if st.button("Sign Up"):
                if register(r_user, r_pass):
                    st.success("Account created! Please log in.")
                else:
                    st.error("Username taken or error occurred.")

# --- MAIN PAGE ---
st.title("🕵️‍♂️ Truth Seeker AI")
st.markdown("### Detect Fake News with Neural Networks")

if st.session_state.token:
    # User is Logged In
    news_text = st.text_area("Paste the News Article/Headline here:", height=150)
    
    if st.button("Analyze Truth 🔍"):
        if len(news_text) < 10:
            st.warning("Please enter at least 10 characters.")
        else:
            with st.spinner("Consulting the oracle..."):
                result = get_prediction(news_text, st.session_state.token)
            
            if "error" in result:
                st.error(f"Error: {result['error']}")
            else:
                # Display Results
                prediction = result['prediction']
                confidence = result['confidence_score']
                
                # Visual Logic
                if prediction == "Real News":
                    st.success(f"## ✅ Verdict: {prediction}")
                    st.balloons()
                else:
                    st.error(f"## 🚨 Verdict: {prediction}")
                
                # Confidence Meter
                st.progress(confidence)
                st.caption(f"Model Confidence: {confidence*100:.2f}%")

else:
    # User is Logged Out
    st.info("👋 Please **Login** via the sidebar to access the Neural Network.")
    st.image("https://media.giphy.com/media/3o7btUg31OCi0NXdkY/giphy.gif") # Optional fun GIF

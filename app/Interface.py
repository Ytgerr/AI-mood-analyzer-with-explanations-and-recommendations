import streamlit as st
import requests
import time
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np

def get_time_period():
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "morning"
    elif 12 <= hour < 21:
        return "noon"
    else:
        return "night"

st.set_page_config(page_title="AI Mood Analyzer", page_icon="🧠", layout="centered")

for key in ["login", "password", "age"]:
    if key not in st.session_state:
        st.session_state[key] = None

st.markdown("<h1 style='text-align: center;'>🧠 AI Mood Analyzer</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>✨ Understand your mood through text using AI-powered analysis.</p>", unsafe_allow_html=True)

st.markdown("#### 🔒 We respect your privacy")
st.caption("Your data is only used for analysis during this session and is not stored permanently.")

with st.expander("ℹ️ What is this app?"):
    st.markdown("""
    This AI-powered tool analyzes your written text and provides insights into the mood behind your message.
    
    - Uses two models: **Simple** (fast) and **Advanced** (deep analysis)
    - Takes into account your **age** and **time of day**
    - Shows mood trends and dynamics
    - Lets you confirm or correct AI predictions
    """)

st.divider()
col1, col2, col3 = st.columns([1, 2, 1])

@st.dialog("🔓 Login to your account")
def login_dialog():
    with st.form("login_form"):
        login = st.text_input(" Username")
        password = st.text_input(" Password", type="password")
        submit = st.form_submit_button("Login")
        if submit:
            try:
                with open("users.txt") as file:
                    for line in file:
                        parts = line.strip().split(" ")
                        if len(parts) == 3:
                            file_log, file_pass, age = parts
                            if login == file_log and password == file_pass:
                                st.success("✅ Logged in successfully!")
                                st.session_state.login = login
                                st.session_state.password = password
                                st.session_state.age = int(age)
                                time.sleep(1.5)
                                st.rerun()
                st.error("❌ Incorrect username or password.")
            except FileNotFoundError:
                st.error("⚠️ User database not found.")

@st.dialog("📝 Create your account")
def reg_dialog():
    with st.form("reg_form"):
        login = st.text_input("Choose a username")
        password = st.text_input("Create a password", type="password")
        age = st.number_input("Your age (optional but helps analysis)", min_value=1, max_value=110)
        submit = st.form_submit_button("Register")
        if submit:
            with open("users.txt", "a") as file:
                file.write(f"{login} {password} {int(age)}\n")
            st.session_state.login = login
            st.session_state.password = password
            st.session_state.age = int(age)
            st.success("Registration successful! Redirecting to main page...")
            time.sleep(1.5)
            st.rerun()


if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "feedback_submitted" not in st.session_state:
    st.session_state.feedback_submitted = False
if "feedback_message" not in st.session_state:
    st.session_state.feedback_message = ""

if st.session_state.login is None:
    st.markdown("<h3 style='text-align: center;'>👤 Please log in or register</h3>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
        login_btn = st.button("🔓 Login")
        reg_btn = st.button("📝 Register")
        st.markdown("</div>", unsafe_allow_html=True)
    if login_btn:
        login_dialog()
   
    if reg_btn:
        reg_dialog()
else:
    st.sidebar.header(f"Welcome, {st.session_state.login}", divider="rainbow")
    if st.sidebar.button("Logout"):
        st.session_state.login = None
        st.session_state.password = None
        st.session_state.age = None
        st.session_state.analysis_result = None
        st.session_state.feedback_submitted = False
        st.session_state.feedback_message = ""
        st.rerun()

    st.sidebar.subheader("💡 Choose a model")
    st.sidebar.write("""
    **Simple Model**: A basic model that analyzes text sentiment with fewer parameters. It is faster but might be less accurate.
    
    **Advanced Model**: This model uses additional features and more advanced algorithms to achieve better accuracy. It may take more time to analyze text but provides more detailed results.
    """)
    chosen_model = st.sidebar.selectbox("Choose the model", ['simple', 'advance'])

    st.write("Chosen model:", chosen_model)
    time_of_day = get_time_period()

    with st.form(key="text_analysis_form"):
        text_input = st.text_input("Enter a message or short text describing how you feel.", placeholder= "E.g. I'm feeling a bit tired today")
        st.caption("The AI will analyze the emotional tone of your message.")
        submit_button = st.form_submit_button("Send")

        if submit_button and text_input:
            st.session_state.analysis_result = None
            st.session_state.feedback_submitted = False
            st.session_state.feedback_message = ""
            with st.spinner('Analyzing your text...'):
                try:
                    response = requests.post(
                        "http://localhost:8000/process/",
                        json={
                            "text": text_input,
                            "model": chosen_model,
                            "time": time_of_day,
                            "age": st.session_state.age
                        }
                    )
                    if response.status_code == 200:
                        st.session_state.analysis_result = response.json()
                    else:
                        st.session_state.analysis_result = {"error": "Server error"}
                except Exception as e:
                    st.session_state.analysis_result = {"error": f"Error: {e}"}

    if st.session_state.analysis_result:
        data = st.session_state.analysis_result
        if "error" in data:
            st.error(data["error"])
        else:
            time_record = time.time()
            t_struct = time.localtime(time_record)
            with open("scores.txt", "a") as file:
                file.write(f"{st.session_state.login} {data['label']} {get_time_period()} {time.strftime('%Y-%m-%d %H:%M:%S', t_struct)}\n")
            st.subheader("● Mood Analysis Result")
            label_color = {
                "Positive": "#34c759", 
                "Neutral": "#ff9500",   
                "Negative": "#ff3b30"  
            }
            mood_label = data['label']
            st.markdown(
                f"<p style='font-size: 20px;'>Predicted Mood: "
                f"<span style='color: {label_color.get(mood_label, '#000')}; font-weight: bold;'>{mood_label}</span></p>",
                unsafe_allow_html=True
            )

            st.subheader("● Why this result?")
            st.markdown("The AI analyzed your message and found the following words influencing the emotional tone:")

            def get_score_color(score):
                if score > 0.1:
                    return "#34c759"  
                elif score < -0.1:
                    return "#ff3b30" 
                else:
                    return "#ff9500" 

            for item in data["explanation"]:
                word = item["word"]
                score = item["score"]
                color = get_score_color(score)
                st.markdown(
                    f"<p style='font-size: 16px;'>• "
                    f"<span style='font-weight: bold;'>{word}</span> → "
                    f"<span style='color: {color}; font-weight: bold;'>influence score: {score:+.2f}</span></p>",
                    unsafe_allow_html=True
                )

            st.markdown(
                f"<p>These words are typical for a "
                f"<span style='font-weight:bold; color:{label_color.get(mood_label, '#000')}'>{mood_label}</span> mood, "
                f"so the model made this prediction.</p>",
                unsafe_allow_html=True
            )
            if st.button("Plot a 1-day mood graph"):

                time_ranges = ("morning", "noon", "evening","night")
                time_index = {
                    "morning": 0,
                    "noon": 1,
                    "evening": 2,
                    "night": 3
                }
                with open("scores.txt") as file:
                    positives= [0]*4
                    neutrals= [0]*4
                    negatives = [0]*4
                    for line in file:
                        name, label, time_range, date, date_time = line.strip().split(" ")
                        idx = time_index.get(time_range, None)
                        if idx is not None:
                            if label == "Positive":
                                positives[idx] += 1
                            elif label == "Neutral":
                                neutrals[idx] += 1
                            else:
                                negatives[idx] += 1
                day_figures = {
                    'Positives': (positives[0],positives[1],positives[2],positives[3]),
                    'Neutrals': (neutrals[0],neutrals[1],neutrals[2],neutrals[3]),
                    'Negatives': (negatives[0],negatives[1],negatives[2],negatives[3]),
                }

                x = np.arange(len(time_ranges))
                width = 0.25
                multiplier = 0

                fig, ax = plt.subplots(layout='constrained')
                colors = {
                    'Positives': '#4CAF50',  
                    'Neutrals': '#FFC107',   
                    'Negatives': '#F44336'
                }
                for attribute, measurement in day_figures.items():
                    offset = width * multiplier
                    rects = ax.bar(x + offset, measurement, width, label=attribute, color=colors.get(attribute, '#999999'))
                    ax.bar_label(rects, padding=3)
                    multiplier += 1
                    
                ax.set_ylabel('Count')
                ax.set_title('Mood dynamic by a time period')
                ax.set_xticks(x + width, time_ranges)
                ax.legend(loc='upper left', ncols=3)
                all_counts = positives + neutrals + negatives
                y_max = max(all_counts) if all_counts else 0
                y_top = y_max * 1.2
                ax.set_ylim(0, y_top)
                st.pyplot(fig)
                
            st.subheader("📢 Feedback")
            with st.form(key="feedback_form"):
                feedback = st.radio(
                    "Do you think the answer was correct?",
                    ("True", "False"),
                    key="feedback_radio"
                )

                report_option = None
                if feedback == "False":
                    report_option = st.selectbox(
                        "What should the correct label be?",
                        ["Negative", "Neutral", "Positive"],
                        key="report_selectbox"
                    )

                submit_feedback = st.form_submit_button("Submit feedback")

                if submit_feedback:
                    if feedback == "False" and report_option:
                        st.session_state.feedback_message = f"✅ Thanks! You marked it as incorrect. Correct label should be: {report_option}"
                    else:
                        st.session_state.feedback_message = "✅ Thanks! You confirmed the result is correct."
                    st.session_state.feedback_submitted = True

            if st.session_state.feedback_submitted:
                st.success(st.session_state.feedback_message)
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


@st.dialog("Login with credentials")
def login_dialog():
    with st.form("login_form"):
        login = st.text_input("Username")
        password = st.text_input("Password")
        submit = st.form_submit_button("Submit")
        if submit:
            with open("users.txt") as file:
                for line in file:
                    file_log, file_pass, age = line.strip().split(" ")
                    if login == file_log and password == file_pass:
                        st.success("Logged in successfully")
                        st.session_state.login = file_log
                        st.session_state.password = file_pass
                        st.session_state.age = int(age)
                        st.rerun()
            st.error("Wrong credentials")


@st.dialog("Registration form")
def reg_dialog():
    with st.form("reg_form"):
        login = st.text_input("Username")
        password = st.text_input("Password")
        st.write("To improve the accuracy of the analysis, please indicate your age. This will help us better take into account the peculiarities of mood perception depending on age.")
        age = st.number_input("Age", min_value=1, max_value=110, step=1)
        submit = st.form_submit_button("Submit")
        if submit:
            with open("users.txt", "a") as file:
                file.write(f"{login} {password} {int(age)}\n")
            st.session_state.login = login
            st.session_state.password = password
            st.session_state.age = int(age)
            st.success("Registration successful! You are now logged in.")
            st.write("You will now be redirected to the main page.")
            time.sleep(2)
            st.rerun()


st.title("AI Mood Analyzer")

if "login" not in st.session_state:
    st.session_state.login = None
if "password" not in st.session_state:
    st.session_state.password = None
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "feedback_submitted" not in st.session_state:
    st.session_state.feedback_submitted = False
if "feedback_message" not in st.session_state:
    st.session_state.feedback_message = ""

if st.session_state.login is None:
    login_btn = st.button("Login")
    if login_btn:
        login_dialog()
    reg_btn = st.button("Register")
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
        text_input = st.text_input("Write text:")
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
                file.write(f"{st.session_state.login} {data["label"]} {get_time_period()} {time.strftime("%Y-%m-%d %H:%M:%S", t_struct)}\n")
            st.subheader("Result of analyze:")
            st.write("Responce: ", data["label"])

            st.subheader("💡 Explanation:")
            st.write(
                f"The model determined that the message was categorized as {data['label']} because it contained the words:")
            for item in data["explanation"]:
                word = item["word"]
                score = item["score"]
                st.write(f"- **{word}** → influence: {score:+}")
            st.write(
                f"These words are characteristic of a {data['label']} mood, and they determined the algorithm of the final decision.")

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

                for attribute, measurement in day_figures.items():
                    offset = width * multiplier
                    rects = ax.bar(x + offset, measurement, width, label=attribute)
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

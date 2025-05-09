import streamlit as st
import requests
import time
from datetime import datetime

# login_dialog и reg_dialog - это окошки, вызываемые при
# нажатии соответствующих кнопок


def get_time_period():
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "morning"
    elif 12 <= hour < 17:
        return "noon"
    elif 17 <= hour < 21:
        return "evening"
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

# Инициализация логина и пароля в session_state
# для первого захода (как я понял)

if "login" not in st.session_state:
    st.session_state.login = None
if "password" not in st.session_state:
    st.session_state.password = None

# Проверка наличия логина
# Если его нет - показываются кнопки регистрации и логина
# Если есть - Показывается всё остальное: выбор модели, инпут и т.д.

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
        st.rerun()

    st.sidebar.subheader("💡 Choose a model")
    st.sidebar.write("""
    **Simple Model**: A basic model that analyzes text sentiment with fewer parameters. It is faster but might be less accurate.
    
    **Advanced Model**: This model uses additional features and more advanced algorithms to achieve better accuracy. It may take more time to analyze text but provides more detailed results.
    """)
    chosen_model = st.sidebar.selectbox(
        "Choose the model", ['simple', 'advance'])

    st.write("Chosen model:", chosen_model)
    time_of_day = get_time_period()

    text_input = st.text_input("Write text:")

    if st.button("Send"):

        if text_input:
            with st.spinner('Analyzing your text...'):
                try:
                    response = requests.post(
                        "http://localhost:8000/process/", json={"text": text_input,
                                                                "model": chosen_model,
                                                                "time": time_of_day,
                                                                "age": st.session_state.age
                                                                }
                    )
                    if response.status_code == 200:
                        data = response.json()
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
                    else:
                        st.error("Error")
                except Exception as e:
                    st.error(f"Error: {e}")

import streamlit as st
import requests

# login_dialog и reg_dialog - это окошки, вызываемые при
# нажатии соответствующих кнопок

@st.dialog("Login with credentials")
def login_dialog():
    with st.form("login_form"):
        login = st.text_input("Username")
        password = st.text_input("Password")
        submit = st.form_submit_button("Submit")
        if submit:
            with open("users.txt") as file:
                for line in file:
                    file_log,file_pass = line.strip().split(" ")
                    if login == file_log and password == file_pass:
                        st.success("Logged in successfully")
                        st.session_state.login =  file_log
                        st.session_state.password = file_pass
                        st.rerun()
            st.error("Wrong credentials")

@st.dialog("Registration form")
def reg_dialog():
    with st.form("reg_form"):
        login = st.text_input("Username")
        password = st.text_input("Password")
        submit = st.form_submit_button("Submit")
        if submit:
            with open("users.txt","a") as file:
                file.write(f"{login} {password}\n")
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
    st.sidebar.header(f"Welcome, {st.session_state.login}",divider="rainbow")
    if st.sidebar.button("Logout"):
        st.session_state.login = None
        st.session_state.password = None
        st.rerun()

    chosen_model = st.sidebar.selectbox("Choose the model", ['chatGPT 14.5','T-800'])
    st.write("Chosen model:", chosen_model)

    text_input = st.text_input("Write text:")
    if st.button("Send"):
        if text_input:
            response = requests.post(
                "http://localhost:8000/process/", json={"text": text_input}
            )
            if response.status_code == 200:
                data = response.json()
                st.subheader("Result of analyze:")
                st.write("Responce: ", data["label"])

                st.subheader("💡 Explanation:")
                st.write(f"The model determined that the message was categorized as {data['label']} because it contained the words:")
                for item in data["explanation"]:
                    word = item["word"]
                    score = item["score"]
                    st.write(f"- **{word}** → influence: {score:+}")
                st.write(f"These words are characteristic of a {data['label']} mood, and they determined the algorithm of the final decision.")
            else:
                st.error("Error")

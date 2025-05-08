import streamlit as st
import requests

st.title("AI Mood Analyzer")

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

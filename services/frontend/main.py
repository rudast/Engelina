import os
import requests
import streamlit as st

API_BASE = os.getenv("BACKEND_API_URL", "http://localhost:8000")
st.write("API_BASE =", API_BASE)  # можно убрать потом

st.set_page_config(page_title="English Text Checker", layout="centered")

def load_css(path="style.css"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass

load_css()

st.title("English Text Checker")

user_id = st.number_input("User ID", min_value=1, value=1, step=1)
level = st.selectbox("Level", ["A1", "A2", "B1", "B2", "C1"])
text = st.text_area("Enter your text", height=220)

if st.button("Check", type="primary", use_container_width=True):
    if not text.strip():
        st.error("Text cannot be empty.")
    else:
        with st.spinner("Checking..."):
            r = requests.post(
                f"{API_BASE}/api/check",
                json={"user_id": int(user_id), "text": text, "level": level},
                timeout=60,
            )
        if r.ok:
            data = r.json()
            st.subheader("Corrected text")
            st.write(data.get("corrected_text", ""))

            st.subheader("Explanation")
            st.write(data.get("explanation", ""))

            st.subheader("Errors")
            errs = data.get("errors", [])
            if not errs:
                st.success("No errors")
            else:
                for e in errs:
                    st.write(f"- {e.get('type')} / {e.get('subtype','-')}: {e.get('original')} → {e.get('corrected')}")
        else:
            st.error(f"Backend error: {r.status_code}")
            st.code(r.text)

# test_app.py
import streamlit as st
st.set_page_config(page_title="Test", layout="wide")
st.title("Streamlit Minimal Test")
st.write("hello ra — if you see this, Streamlit is working.")
if st.button("Click me"):
    st.write("Button clicked!")

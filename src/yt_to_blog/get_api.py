import streamlit as st

# Function to get api key from user if not already set
@st.dialog("Enter Your API Keys")
def get_api():
    openai = st.text_input("OpenAI API Key", type="password", help="Your API key remains secure and is not saved.")
    st.markdown("[Create your OpenAI API Key](https://platform.openai.com/api-keys)", unsafe_allow_html=True)
    
    gemini = st.text_input("Google Gemini API Key", type="password", help="Your API key remains secure and is not saved.")
    st.markdown("[Create your Gemini API Key](https://aistudio.google.com/apikey)", unsafe_allow_html=True)
    
    if st.button("Submit"):
        if openai and gemini:
            st.session_state.api_keys["OPENAI_API_KEY"] = openai
            st.session_state.api_keys["GOOGLE_API_KEY"] = gemini
            st.success("API key set successfully!")
            st.rerun()
        else:
            st.error("API key cannot be empty.")
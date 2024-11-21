# these three lines swap the stdlib sqlite3 lib with the pysqlite3 package
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

# Streamlit app
import io
import os
from dotenv import load_dotenv
import time
import streamlit as st
from PIL import Image

# Required modules
from crew import YtToBlogCrew
from tools.custom_tool import VideoHandler # Handles URL validity check, video id extraction and transcription

from get_api import get_api

# Page title
st.set_page_config(page_title="YouTube Video to Blogpost", page_icon="favicon.svg")

# Loading API Keys
load_dotenv()

# Check if the API key is set
if "api_keys" not in st.session_state:
    st.session_state.api_keys = {}
    if "OPENAI_API_KEY" not in os.environ or "GOOGLE_API_KEY" not in os.environ:
        get_api()
    else:
        st.session_state.api_keys["OPENAI_API_KEY"] = os.environ["OPENAI_API_KEY"]
        st.session_state.api_keys["GOOGLE_API_KEY"] = os.environ["GOOGLE_API_KEY"]

if ("GOOGLE_API_KEY" in st.session_state.api_keys) and ("OPENAI_API_KEY" in st.session_state.api_keys):

    # Loading App Icon
    icon_file_path = os.path.join("src", "yt_to_blog", "icon.svg")
    icon_svg = open(icon_file_path).read()
    heading = "Video to Blogpost"
    # Setting header format
    header = f'''
        <div style="display: flex; align-items: center;">
            <div style="margin-right: 10px;">{icon_svg}</div>
            <h1>{heading}</h1>
        </div>
        '''
    # Display the icon and header
    st.markdown(header, unsafe_allow_html=True)

    # Initializing chat history for streamlit
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    ## Displaying previous chat on app re-run
    if st.session_state["chat_history"]:
        st.header("Current Thread")
        for message in st.session_state.chat_history:
            st.chat_message(message["role"]).write(message["content"])

    # Function to refresh sidebar everytime a new title is added
    def populate_sidebar():
        side_heading = "History"
        # Setting header format
        side_header = f'''
            <div style="display: flex; align-items: center;">
                <div style="margin-right: 10px;">{icon_svg}</div>
                <h1>{side_heading}</h1>
            </div>
            '''
        with st.sidebar:
            st.markdown(side_header, unsafe_allow_html=True)
            for file in st.session_state.blog_history:
                st.download_button(label=file["title"], data=file["response"], file_name=file["title"],
                                                            on_click=lambda: write(message="File Downloaded.", role="assistant"),
                                                            key=file["title"])

    # Initializing blog_history to store previously created posts
    # Also initiating sidebar
    if "blog_history" not in st.session_state:
        st.session_state.blog_history = []

    populate_sidebar()


    # Function to write to streamlit app and store to chat history
    def write(message, role):
        # Display message
        st.chat_message(role).write(message)
        # Store in streamlit chat history
        st.session_state.chat_history.append({"role": role, "content": message})


    def run(url):
        """
        Run the crew.
        """
        inputs = {
            'url': url}
        
        return YtToBlogCrew(st.session_state.api_keys["OPENAI_API_KEY"]).crew().kickoff(inputs=inputs)

    # Chat input
    text = st.chat_input(placeholder="Paste any YouTube video URL.")

    # User has entered a text
    if text:
        write(message=text, role="user")
        with st.spinner("Accessing video..."):
            time.sleep(2)
            video = VideoHandler(text)
            if not video.is_valid_youtube_url():
                write(message="Please enter a valid YouTube video URL.", role="assistant")
            else:
                video.extract_video_id()
                if video.video_id:
                    video.get_title_thumbnail()
                    if video.title:
                        title = video.title
                        write(message=title, role="assistant")
                    if video.thumbnail:
                        thumbnail = Image.open(io.BytesIO(video.thumbnail))
                        write(message=thumbnail, role="assistant")

        if video.title:           
            with st.spinner("Creating Blogpost..."):
                response = run(text).raw
            
            write(message=response, role="assistant")

            with st.spinner("Creating file..."):
                time.sleep(2)
                if title:
                    # Removing spaces and non-alphanumeric characters using list comprehension
                    file_name = ''.join(char for char in title if char.isalnum())
                    # Create the file name and path
                    file_name = file_name[:20] + ".md"

                    # Download button
                    st.chat_message("assistant").download_button(label="Download File", data=response, file_name=file_name,
                                                                on_click=lambda: write(message="File Downloaded.", role="assistant"), key="chat_download") 
                    
                    # Storing response to blog_history for future downloads
                    st.session_state.blog_history.append({"title": file_name, "response": response})   
        else:
            write(message="Sorry. Video was inaccessible.", role="assistant")              
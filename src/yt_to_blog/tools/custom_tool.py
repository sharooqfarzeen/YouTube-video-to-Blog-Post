from crewai_tools import tool

import os
import io
import re
import requests
from PIL import Image
from bs4 import BeautifulSoup
from youtube_transcript_api import YouTubeTranscriptApi

import logging
from dotenv import load_dotenv

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

import streamlit as st


# Handles URL validity check, video id extraction and transcription
class VideoHandler:

    def __init__(self, url):
        self.url = url # Video URL
        self.video_id = None # Video ID
        self.title = None # YouTube video title
        self.thumbnail = None # YouTube thumbnail
        self.transcript = None # Video transcript

    # Function to check if URL is a valid YouTube address
    def is_valid_youtube_url(self):
        # Regex pattern to check for a valid YouTube URL
        youtube_regex = re.compile(
            r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')
        
        match = youtube_regex.match(self.url)
        return match is not None

    # Function to extract video id from URL
    def extract_video_id(self):
        # Regex to match video ID
        video_id_match = re.search(r"(?:v=|\/v\/|\/embed\/|youtu\.be\/|\/shorts\/|\/watch\?v=|\/videos\/|\/e\/)([^#\&\?]{11})", self.url)
        
        if video_id_match:
            self.video_id = video_id_match.group(1)
        else:
            self.video_id = None

    # Function to extract video title and thumbnail, if available
    def get_title_thumbnail(self):
        # Fetch the YouTube page
        response = requests.get(self.url)
        
        # Check if the request was successful
        if response.status_code != 200:
            self.title = None
            self.thumbnail = None
            return

        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract the video title
        # Find the <meta> tag with name "title"
        meta_title_tag = soup.find('meta', attrs={'name': 'title'})
        self.title = meta_title_tag["content"] if meta_title_tag else None

        # Construct thumbnail URL
        thumbnail_url = f"https://img.youtube.com/vi/{self.video_id}/maxresdefault.jpg"

        response = requests.get(thumbnail_url)

        # Save the image if the request was successful
        self.thumbnail = response.content if (response.status_code == 200) else None

    # Function to retrieve transcript
    def get_transcript(self):
        try:
            language_list = ["en", "en-US", "en-GB", "en-IN", "en-AU", "en-CA", "en-NZ", "en-ZA", "en-PH", 
                            "en-SG", "en-JM", "en-NG", "en-HK", "en-TT", "en-BZ", "en-MY", "en-IE"]
            transcript = YouTubeTranscriptApi.get_transcript(video_id=self.video_id, languages=language_list)
            self.transcript = str(transcript)
        except:
            self.transcript = None


# Gemini
# Configure logging to write to a file, set level to ERROR to log only errors
logging.basicConfig(filename='error.log', level=logging.ERROR, 
                    format='%(asctime)s - %(levelname)s - %(message)s')


def get_response(prompt, api_key):
    try:
        genai.configure(api_key=api_key)

        # Initializing model
        model = genai.GenerativeModel(model_name="gemini-1.5-flash",
                                    system_instruction=
                                    """
                                    You are a YouTube video transcript summarizer.
                                    
                                    Most of your inputs will have 3 parameters:
                                        1. The YouTube video title
                                        2. The video thumbnail, which is an image
                                        3. The video transcript
                                        
                                        The YouTube video transcripts will be in the following format:
                                        [{'text': "",
                                        'start': ,
                                        'duration':},
                                        .
                                        .
                                        .
                                        ]
                                        
                                        Your job is to go through the video title, thumbnail and transcript to form a point by point 
                                        summary of the video.
                                        The length of the summary should be directly proportional to video length.
                                        The sentiment and style of summary should reflect the topic of the video and should sound like a human.
                                    
                                    Some inputs may not have all 3 parameters. User the parameters in hand to create the point by point summary.
                                    """)

        chat = model.start_chat()


        # Fetching response
        response = chat.send_message(
            prompt, 
            safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE
    }
    )
        return response.text   
    
    except Exception as e:
        
        # Logging the error
        logging.error(str(e), exc_info=True)

        error_msg = "Query not Supported"
        
        return error_msg


# Crew AI Tool            
@tool("YouTube Summarizer")
def summarize(url: str):
    """Takes in a YouTube video URL and returns a point by point summary of topics discussed in the video"""
 
    # Initiate Video Handler Object with the "URL"
    video = VideoHandler(url)
    # If it is not a valid YouTube URL
    if not video.is_valid_youtube_url():
        return "Invalid YouTube video URL."
    # URL is valid
    else:
        # Extract video id - video_id will be set to None if not accessible
        video.extract_video_id()
        # If video was not accessible
        if not video.video_id:
            return "URL Inaccessible"
        # If video was accessible
        else:
            prompt = []
            # Get video title and thumbnail, if available
            video.get_title_thumbnail()
            # If thumbnail was available  
            if video.thumbnail:
                # Saving as Image for UI rendition
                image = Image.open(io.BytesIO(video.thumbnail))
                # Add to prompt
                prompt.append(image)
    
            # If title was available
            if video.title:
                # Adding to prompt
                prompt.append("Video Title: " + video.title)

                        
            # Generate transcript
            video.get_transcript()

            # If a transcript was not available
            if not video.transcript:
                return "Transcript not available for the video. Please try another URL."
            else:
                prompt.append(video.transcript)
                # Streaming summary from model and writing it to UI
                with st.spinner("Analyzing video..."):
                    response = get_response(prompt, st.session_state.api_keys["GOOGLE_API_KEY"])

    return response
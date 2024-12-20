#!/usr/bin/env python
import sys
from crew import YtToBlogCrew

# This main file is intended to be a way for your to run your
# crew locally, so refrain from adding necessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run(url):
    """
    Run the crew.
    """
    inputs = {
        'url': url}
    
    YtToBlogCrew().crew().kickoff(inputs=inputs)
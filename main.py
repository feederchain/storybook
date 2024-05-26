#!/usr/bin/env python3

"""
A program that generates storybook pages with Ollama and Stable Diffusion for the Inky Impression
"""

import os
import json
import math
import requests
import subprocess
import time
from PIL import Image, ImageDraw, ImageFont
from inky.auto import auto

display = auto()

GENERATION_INTERVAL = 6 #seconds
DISPLAY_RESOLUTION = (448, 600)
TOTAL_LINES = 6
OLLAMA_API = 'http://localhost:11434/api/generate'
OLLAMA_MODEL = 'llama3'

BOOK_DIR = 'book1/'
STORYBOOK = BOOK_DIR + 'storybook.json'

PERSONA = '''You are a machine that generates text for children\'s books. 
You only generate text. 
You do not reply with the text in quotes, quotes are allowed just not around the reply.  
You do not preface the reply with anything. 
You do not explain your replies. '''.replace("\n","")

OLLAMA_PROMPT = '''Create text from the page of an illustrated children\'s fantasy book. 
This text should be around 20 words. If you desire, you can include a hero, monster, mythical 
creature or artifact. You can choose a random mood or theme. Be creative.'''.replace("\n", "")

STORY_PROMPT = '''Create the text for the next page. Given the following  
page numbers and text of a illustrated children\'s fantasy book. '''.replace("\n","")

HOME = os.path.expanduser("~")
SD_LOCATION = HOME + '/OnnxStream/src/build/sd'
SD_MODEL_PATH = HOME + '/sd_models/stable-diffusion-1.5-onnxstream'

SD_PROMPT = 'an illustration in a children\'s book for the following scene: '

SD_STEPS = 3
FONT_FILE = 'CormorantGaramond-Regular.ttf'
FONT_SIZE = 21

def get_story(prompt):
    r = requests.post(OLLAMA_API, timeout=600,
        json = {
            'model': OLLAMA_MODEL,
            'prompt': prompt,
            'stream': False,
            'options': {
              'temperature': 1.0
            }
        })
    data = r.json()
    return data['response'].lstrip()

# warp text by adding a newline at the last space before the max_length,
# respecting pre-existing newlines as natural breaks for re-starting the character count
def wrap_text(text, max_length=50):
    final_text = ""
    # Split the text into lines based on existing newlines
    lines = text.split('\n')
    
    for line in lines:
        while len(line) > max_length:
            # Find the last space before max_length
            wrap_index = line.rfind(' ', 0, max_length)
            # If no space is found within the range, wrap at max_length
            if wrap_index == -1:
                wrap_index = max_length
            # Append wrapped line to result and remove the processed part
            final_text += line[:wrap_index].strip() + '\n'
            line = line[wrap_index:].lstrip()
        # Append the remaining part of the line
        final_text += line + '\n'
    
    # Remove the last unnecessary newline added
    return final_text.strip()


def load_storybook(file_path):
    if os.path.isfile(file_path):
        with open(file_path, 'r') as file:
            try:
                data = json.load(file)
                return data
            except json.JSONDecodeError:
                return []
    return []


def save_storybook(file_path, text):
    data = load_storybook(file_path)
    
    # Determine the next page number
    if data:
        max_page_number = max(entry["page_number"] for entry in data)
        next_page_number = max_page_number + 1
    else:
        next_page_number = 1
    
    # Append the new entry
    new_entry = {"page_number": next_page_number, "text": text}
    data.append(new_entry)
    
    # Write the updated data back to the file
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)
    return next_page_number


def convert(data):
    """Convert JSON data to a formatted text string."""
    formatted_text = ""
    
    for entry in data:
        formatted_text += f"Page {entry['page_number']}: {entry['text']}\n"
    
    return formatted_text


def generate_page():
    story = load_storybook(STORYBOOK)
    #print(convert(story))
    prompt = PERSONA + STORY_PROMPT + convert(story) + OLLAMA_PROMPT
    #print(prompt)
    generated_text = get_story(prompt).replace("\n\n","\n")
    print(f'text: {generated_text}')

    page = "page_" + str(save_storybook(STORYBOOK, generated_text))
    temp_image = BOOK_DIR + page + "_image.png"
    #return
    subprocess.run([SD_LOCATION, '--xl', '--turbo', '--rpi', '--models-path', SD_MODEL_PATH,\
                    '--prompt', SD_PROMPT+f'"{generated_text}"',\
                    '--steps', f'{SD_STEPS}', '--output', temp_image], check=False) 
    generated_text = wrap_text(generated_text, 53)
    canvas = Image.new(mode="RGB", size=DISPLAY_RESOLUTION, color="white")
    im2 = Image.open(temp_image)
    im2 = im2.resize((448,448))
    canvas.paste(im2)
    im3 = ImageDraw.Draw(canvas)
    font = ImageFont.truetype(FONT_FILE, FONT_SIZE)
    im3.text((7, 450), generated_text, font=font, fill=(0, 0, 0))
    canvas.show()
    canvas.save(BOOK_DIR + page + '.png') # save a local copy for closer inspection
    canvas = canvas.rotate(90,expand=1)
    display.set_image(canvas)
    display.show()

def main():
    while True:
        generate_page()
        for _ in range(GENERATION_INTERVAL):
            if os.path.isfile('stop'):
                print("Stop file found. Exiting loop.")
                return
            time.sleep(1)  # Check for the stop file every second

if __name__ == '__main__':
    main()

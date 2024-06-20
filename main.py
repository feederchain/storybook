#!/usr/bin/env python3

"""
A program that generates storybook pages with Ollama and Stable Diffusion for the Inky Impression
"""

import sys
import os
import json
import math
import time
import signal
import threading
from PIL import Image, ImageDraw, ImageFont
from inky.auto import auto
from config import load_config, load_api_keys, get_llm
from gpiozero import Button


display = auto()

GENERATION_INTERVAL = 600 #seconds
DISPLAY_RESOLUTION = (448, 600)
TOTAL_LINES = 6

BOOK_DIR = 'book1/'
STORYBOOK = BOOK_DIR + 'storybook.json'
CONFIG = 'config.json'
KEYS = 'api_keys.json'

# Gpio pins for each button (from top to bottom)
BUTTONS = [5, 6, 16, 24]

# These correspond to buttons A, B, C and D respectively
LABELS = ['A', 'B', 'C', 'D']

button_lock = threading.Lock()

current_page = 0
max_page = 0


def handle_button(pin):
    global current_page
    if button_lock.locked():
        return
    
    with button_lock:
        label = LABELS[BUTTONS.index(pin.pin.number)]
        print("Button press detected on pin: {} label: {}".format(pin.pin.number, label))
        if label == 'A':
            if current_page >= max_page:
                generate_page()
            elif current_page >= 1:
                current_page += 1
                load_page(current_page)
        elif label == 'B':
            os.kill(os.getpid(), signal.SIGUSR1)
        elif label == 'C':
            pass
        elif label == 'D':
            if current_page > 1:
                current_page -= 1
                load_page(current_page)


for pin in BUTTONS:
    button = Button(pin=pin, pull_up=True, bounce_time=0.250)
    button.when_pressed = handle_button


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
    global current_page
    if os.path.isfile(file_path):
        with open(file_path, 'r') as file:
            try:
                data = json.load(file)
                current_page = max(entry["page_number"] for entry in data)
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
    global current_page, max_page
    config = load_config(CONFIG)
    api_keys = load_api_keys(KEYS)
    llm = get_llm(config, api_keys)
    PERSONA = config['PERSONA']
    LLM_PROMPT = config['LLM_PROMPT']
    STORY_PROMPT = config['STORY_PROMPT']
    IMAGE_PROMPT = config['IMAGE_PROMPT']
    FONT_FILE = config['FONT_FILE']
    FONT_SIZE = config['FONT_SIZE']
    
    story = load_storybook(STORYBOOK)
    page_type = "first" if not story else "next"
    prefix = STORY_PROMPT if story else ""
    prompt = prefix + convert(story) + LLM_PROMPT.format(page_type)
    generated_text = llm.generate_text(PERSONA, prompt).replace("\n\n","\n")
    print(f'text: {generated_text}')
    
    current_page = save_storybook(STORYBOOK, generated_text)
    max_page = current_page
    page_string = "page_" + str(current_page)
    temp_image = BOOK_DIR + page_string + "_image.png"
    llm.get_image(IMAGE_PROMPT+f'"{generated_text}"', temp_image) 
    generated_text = wrap_text(generated_text, 53)
    canvas = Image.new(mode="RGB", size=DISPLAY_RESOLUTION, color="white")
    im2 = Image.open(temp_image)
    im2 = im2.resize((448,448))
    canvas.paste(im2)
    im3 = ImageDraw.Draw(canvas)
    font = ImageFont.truetype(FONT_FILE, FONT_SIZE)
    im3.text((7, 450), generated_text, font=font, fill=(0, 0, 0))
    #canvas.show()
    canvas.save(BOOK_DIR + page_string + '.png') # save a local copy for closer inspection
    canvas = canvas.rotate(90,expand=1)
    display.set_image(canvas)
    display.show()


def load_page(page):
    image = BOOK_DIR + "page_" + str(page) + '.png'
    print(image)
    canvas = Image.open(image)
    canvas = canvas.rotate(90,expand=1)
    
    display.set_image(canvas)
    display.show()


def main():
    global current_page, max_page
    if not os.path.exists(BOOK_DIR):
        os.makedirs(BOOK_DIR)
    
    load_storybook(STORYBOOK)
    if current_page > 0:
        max_page = current_page
        load_page(current_page)
    signal.pause()
#     while True:
#         generate_page()
#         for _ in range(GENERATION_INTERVAL):
#             if os.path.isfile('stop'):
#                 print("Stop file found. Exiting loop.")
#                 return
#             time.sleep(1)  # Check for the stop file every second

if __name__ == '__main__':
    main()

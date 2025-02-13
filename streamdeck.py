import os 
import threading
from networktables import NetworkTables
from ntcore import *
from networktables.util import ntproperty
from PIL import Image, ImageDraw, ImageFont
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper
import ntcore

# The following code is added to set the location of the project folder.
project_folder = os.path.dirname(__file__) 
os.environ['PATH'] = project_folder + os.pathsep + os.environ['PATH']

#button images path
ASSETS_PATH = os.path.join(os.path.dirname(__file__), "Assets")
FONT = "arial.ttf"

# Image pairs: True_image, False_image

imageNames = [  
                ("3-ON", "3-OFF"),
                ("10-ON", "10-OFF"),
                ("empty", "empty"),
                ("empty", "empty"),
                ("empty", "empty"),
                ("empty", "empty"),
                ("9-ON", "9-OFF"),
                ("4-ON", "4-OFF"),

                ("2-ON", "2-OFF"),
                ("11-ON", "11-OFF"),
                ("empty", "empty"),
                ("empty", "empty"),
                ("empty", "empty"),
                ("empty", "empty"),
                ("8-ON", "8-OFF"),
                ("5-ON", "5-OFF"),

                ("1-ON", "1-OFF"),
                ("12-ON", "12-OFF"),
                ("empty", "empty"),
                ("empty", "empty"),
                ("empty", "empty"),
                ("empty", "empty"),
                ("7-ON", "7-OFF"),
                ("6-ON", "6-OFF"),

                ("red", "red"),
                ("red", "red"),
                ("empty", "empty"),
                ("empty", "empty"),
                ("empty", "empty"),
                ("empty", "empty"),
                ("blue", "blue"),
                ("blue", "blue")
              ]

# Button styles: Style_name, Style_font, Text
#
# Toggle: Button toggles state when pressed.
# Momentary: Button is true when pressed, false when release

buttonStyles = [
                 ("ToteToggle", FONT, ""),
                 ("ToteToggle", FONT, ""),
                 ("Momentary", FONT, ""),
                 ("Momentary", FONT, ""),
                 ("Momentary", FONT, ""),
                 ("Momentary", FONT, ""),
                 ("ToteToggle", FONT, ""),
                 ("ToteToggle", FONT, ""),

                 ("ToteToggle", FONT, ""),
                 ("ToteToggle", FONT, ""),
                 ("Toggle", FONT, ""),
                 ("Toggle", FONT, ""),
                 ("Toggle", FONT, ""),
                 ("Toggle", FONT, ""),
                 ("ToteToggle", FONT, ""),
                 ("ToteToggle", FONT, ""),

                 ("ToteToggle", FONT, ""),
                 ("ToteToggle", FONT, ""),
                 ("Toggle", FONT, ""),
                 ("Toggle", FONT, ""),
                 ("Toggle", FONT, ""),
                 ("Toggle", FONT, ""),
                 ("ToteToggle", FONT, ""),
                 ("ToteToggle", FONT, ""),

                 ("Image", FONT, ""),
                 ("Image", FONT, ""),
                 ("Toggle", FONT, ""),
                 ("Toggle", FONT, ""),
                 ("Toggle", FONT, ""),
                 ("Toggle", FONT, ""),
                 ("Image", FONT, ""),
                 ("Image", FONT, "")
                ]

global numberOfKeys

#networktables setup

ntinst = ntcore.NetworkTableInstance.getDefault()
ntinst.startClient4("StreamDeck")        # Name of camera in the network table
ntinst.setServerTeam(2635) # How to identify the network table server
ntinst.startDSClient()

sdv = ntinst.getTable("StreamDeck")

global buttonBools

# Generates a custom tile with run-time generated text and custom image via the
# PIL module.
def render_key_image(deck, icon_filename, font_filename, label_text, state):
    # Resize the source image asset to best-fit the dimensions of a single key,
    # leaving a margin at the bottom so that we can draw the key title
    # afterwards.
    icon = Image.open(icon_filename)
    image = PILHelper.create_scaled_image(deck, icon, margins=[0, 0, 0, 0])

    # Load a custom TrueType font and use it to overlay the key index, draw key
    # label onto the image a few pixels from the bottom of the key.
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(font_filename, 14)
    draw.text((image.width / 2, image.height - 20), text=label_text, font=font, anchor="ms", fill="white" if not state else "black")
    # draw.text((10, 10), text=label_text, font=font, anchor="ms", fill="white")

    return PILHelper.to_native_format(deck, image)


# Returns styling information for a key based on its position and state.
# this is run everytime a key is pressed & released
def get_key_style(deck, key, state):
    
    style = { "name": buttonStyles[key][0], 
              "icon": os.path.join(ASSETS_PATH, "{}.png".format(imageNames[key][0 if state else 1])), 
            #   "font": os.path.join(ASSETS_PATH, buttonStyles[key][1]), 
              "font": buttonStyles[key][1], 
              "label": buttonStyles[key][2] }
    return style


# Creates a new key image based on the key index, style and current key state
# and updates the image on the StreamDeck.
def update_key_image(deck, key, state):
    # Determine what icon and label to use on the generated key.
    key_style = get_key_style(deck, key, buttonBools[key])

    # Generate the custom key with the requested image and label.
    image = render_key_image(deck, key_style["icon"], key_style["font"], key_style["label"], state)
    
    # print("Rendering {} to {}".format(key_style["icon"], key))

    # Use a scoped-with on the deck to ensure we're the only thread using it
    # right now.
    with deck:
        # Update requested key with the generated image.
        deck.set_key_image(key, image)

# Prints key state change information, updates rhe key image and performs any
# associated actions when a key is pressed.
def key_change_callback(deck, key, state):

    if key >= numberOfKeys:
        return
    
    # print("{} {}".format( key, state))
    
    key_style = get_key_style(deck, key, state)

    if key_style["name"] == "Toggle":
        if not state:
            return
        else:    
            buttonBools[key] = not buttonBools[key]
    elif key_style["name"] == "Momentary":
        buttonBools[key] = state
    elif key_style["name"] == "ToteToggle":
        for i in range(len(buttonStyles)):
            if buttonStyles[i][0] == "ToteToggle" and buttonBools[i]:
                buttonBools[i] = False
                
                # entry = sdv.getEntry("{}".format(i))
                # entry.setBoolean(False)
                sdv.putBoolean("{}".format(i), False) 
                update_key_image(deck, i, False)


        buttonBools[key] = True
            
    # entry = sdv.getEntry("{}".format(key))
    # entry.setBoolean(True)
    sdv.putBoolean("{}".format(key), buttonBools[key]) 
    if key_style["name"] == "ToteToggle":
        sdv.putString("SelectedProgram", imageNames[key][0])
        sdv.putNumber("SelectedProgramFloat", float(imageNames[key][0].split("-")[0]))
        sdv.putString("SelectedProgramString2", imageNames[key][0].split("-")[0])
    # print("read {}".format(sdv.getBoolean("index{}".format(key), 25)))
    # Update the key image based on the new key state.
    update_key_image(deck, key, buttonBools[key])

    # print("{} is now {}".format(key, buttonBools[key]))
 
if __name__ == "__main__":
    streamdecks = DeviceManager().enumerate()

    print("Found {} Stream Deck(s).\n".format(len(streamdecks)))

    for index, deck in enumerate(streamdecks):
        # This example only works with devices that have screens.
        if not deck.is_visual():
            continue

        deck.open()
        deck.reset()

        print("Opened '{}' device (serial number: '{}', fw: '{}')".format(
            deck.deck_type(), deck.get_serial_number(), deck.get_firmware_version()
        ))

        # Set initial screen brightness to 80%.
        deck.set_brightness(80)
        
        numberOfKeys = deck.key_count()
        
        # print("Deck has {} keys".format(numberOfKeys))
        
        if len(imageNames) != len(buttonStyles):
            continue
        
        if len(imageNames) < numberOfKeys:
            numberOfKeys = len(imageNames)
        
        buttonBools = [False] * numberOfKeys
        
        # Set initial key images.
        for key in range(numberOfKeys):
            update_key_image(deck, key, False)

        # Register callback function for when a key state changes.
        deck.set_key_callback(key_change_callback)

        # Wait until all application threads have terminated (for this example,
        # this is when all deck handles are closed).
        for t in threading.enumerate():
            try:
                t.join()
            except RuntimeError:
                pass

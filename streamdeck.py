import os
import threading
from networktables import NetworkTables
from ntcore import *
from networktables.util import ntproperty
from PIL import Image, ImageDraw, ImageFont
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper
import ntcore

#button images path
ASSETS_PATH = os.path.join(os.path.dirname(__file__), "Assets")
FONT = "arial.ttf"

# Image pairs: True_image, False_image

imageNames = [ ( "bunny0", "empty" ),
               ( "bunny1", "empty" ),
               ( "bunny2", "empty" ),
               ( "bunny3", "empty" ),
               ( "shrimp0", "empty" ),
               ( "shrimp1", "empty" )
              ]

# Button styles: Style_name, Style_font, Text
#
# Toggle: Button toggles state when pressed.
# Momentary: Button is true when pressed, false when release

buttonStyles = [ ( "Toggle", FONT, "hello" ),
                 ( "Toggle", FONT, "world" ),
                 ( "Toggle", FONT, "this" ),
                 ( "Momentary", FONT, "is" ),
                 ( "Momentary", FONT, "a" ),
                 ( "Momentary", FONT, "test" )
                ]

global numberOfKeys

#networktables setup

# ntinst = ntcore.NetworkTableInstance.getDefault()
# ntinst.startClient4("Eclipse")        # Name of camera in the network table
# ntinst.setServerTeam(2635) # How to identify the network table server
# ntinst.startDSClient()

# sdv = ntinst.getTable("StreamDeck")

NetworkTables.initialize(server = "127.0.0.1")
sd = NetworkTables.getTable("SmartDashboard") #interact w/ smartdashboard
sdv = NetworkTables.getTable("Streamdeck") #make table for values to be changed from this script

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
    if key_style["name"] == "Toggle" and state:
        buttonBools[key] = not buttonBools[key]
    elif key_style["name"] == "Momentary":
        buttonBools[key] = state
        
    sdv.putBoolean("boolExample{}".format(key), buttonBools[key]) 
    
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

import keyboard
import mouse
from mouse import WheelEvent
from PIL import ImageGrab
import time

iRank = 0 # index of the current selected window out of the set of windows currently containing the cursor (0 => smallest window containing the cursor will be selected)

def on_scroll(event):
    """
    Callback function triggered when the mouse is scrolled.
    event.delta > 0 means scroll up, event.delta < 0 means scroll down.
    Scroll up increments iRank by 1.
    Scroll down decrements iRank by 1.
    """
    global iRank
    if isinstance(event, WheelEvent): # only action interactions with the scroll wheel
        if event.delta > 0:  # Scroll up
            iRank += 1
            print(f"iRank incremented: {iRank}")
        elif event.delta < 0:  # Scroll down
            iRank -= 1
            print(f"iRank decremented: {iRank}")

def getWindows(img):
    """
    Args:
        img (PIL.Image.Image): image of current screen
    """
    bbox = img.getbbox() # temp return full screen bbox
    windows = [bbox]
    
    return windows

def getCurrentWindow(windows, x, y, iRank):
    return windows[0] # temp return first window


screen = ImageGrab.grab() # capture current screen

windows = getWindows(screen) # output list of windows identified in current screen

# arrange windows in order of increasing area

# Hook scroll events
mouse.hook(on_scroll) # will trigger callback on any mouse event (even moving the cursor)

while True:
    # Exit program if ESC key pressed
    if keyboard.is_pressed("esc"):
        print("\nESC key detected. Exiting...")
        mouse.unhook_all()
        break

    # Save snap if left-click is detected
    if mouse.is_pressed("left"):
        print("\nLeft-click detected. Exiting...")
        # crop() # crop img to region defined by current window
        # tag() # tag the img
        # save() # save the img
        mouse.unhook_all()
        break

    # Temporarily add delay
    time.sleep(0.05)

    # getCursor() # return current position of cursor

    currentWindow = getCurrentWindow(windows,0,0,iRank)     # get currently selected window (input cursor position and currently selected bbox area ranking)
                                            # loop through all windows and update property in window object to indicate if the cursor is inside the window
                                            # output the bbox window with index iRank and capped iRank

    # displayCurrentWindow() # grey out area around the region spanned by the current window


# edit() # bring up GUI to edit tag/annotate screnshot

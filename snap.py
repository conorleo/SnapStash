import keyboard
import matplotlib as mpl
import matplotlib.pyplot as plt
import mouse
from mouse import WheelEvent
from PIL import ImageGrab
import time

# Copy to clipboard
import win32clipboard as clip
import win32con
from io import BytesIO

from windows import Window, getWindows, dispCurrentWindow

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

def copyToClipboard(img):
    """
    Copy image to clipboard.
    Args:
        img (PIL.Image.Image): image of current screen
    """
    output = BytesIO()  # create a BytesIO buffer to hold image data
    img.convert('RGB').save(output, 'BMP')  # convert image to RGB format and save as BMP to the buffer
    data = output.getvalue()[14:]  # extract BMP data, skipping the 14-byte BMP header
    output.close()  # close the buffer

    clip.OpenClipboard()  # open the Windows clipboard
    clip.EmptyClipboard()  # clear any existing clipboard contents
    clip.SetClipboardData(win32con.CF_DIB, data)  # set the clipboard data to the DIB format image
    clip.CloseClipboard()  # close the clipboard

def isCursorInWindow(window, x, y):
    """
    Indicate if point x,y is inside the queried window.
    Args:
        window (Window): Window object.
        x (int): x-position.
        y (int): y-position.
    Returns:
        isInWindow (bool): True implies the point x,y is inside the window. False implies it is outside the window.
    """
    if x > window.bbox[0] and x < window.bbox[2] and y > window.bbox[1] and y < window.bbox[3]:
        return True
    else:
        return False

def getCurrentWindow(windows, x, y, iRank):
    """
    Return currently selected window.
    Args:
        windows (list): List of Window objects present in current screenshot.
        x (int): Cursor x-position on screen.
        y (int): Cursor y-position on screen.
        iRank (int): Index of windows list corresponding to current window.
    Returns:
        curr_window (Window): Current window.
    """
    windowsContainingCursor = [window for window in windows if isCursorInWindow(window, x, y)] # isolate windows containing the cursor

    if len(windowsContainingCursor) == 0:
        return windows[-1] # return full screen (largest area) if cursor is not on the screen

    if iRank != 0: # prevent divide by zero error
        iRank = iRank % len(windowsContainingCursor) # wrap around to smallest bbox if number of valid windows is exceeded
    
    return windowsContainingCursor[iRank]


screen = ImageGrab.grab() # capture current screen

windows = getWindows(screen) # output list of windows identified in current screen

windows = sorted(windows, key=lambda window: window.area) # arrange windows in order of increasing area

# Hook scroll events
mouse.hook(on_scroll) # will trigger callback on any mouse event (even moving the cursor)

# Setup interactive figure
mpl.rcParams['toolbar'] = 'None' # hide navigation toolbar in all figures
plt.ion()  # enable interactive mode
fig = plt.figure()
fig.subplots_adjust(left=0, right=1, top=1, bottom=0)  # remove padding
fig.canvas.manager.full_screen_toggle() # open figure in fullscreen mode
plt.show()

while True:
    # Exit program if ESC key pressed
    if keyboard.is_pressed("esc"):
        print("\nESC key detected. Exiting...")
        mouse.unhook_all()
        break

    # Save snap if left-click is detected
    if mouse.is_pressed("left"):
        print("\nLeft-click detected. Exiting...")
        screenshot = screen.crop(currentWindow.bbox) # crop img to region defined by current window
        # tag() # tag the img
        # save() # save the img
        copyToClipboard(screenshot) # copy screenshot to clipboard
        mouse.unhook_all()
        break

    x, y = mouse.get_position() # return current position of cursor
    # print(x)
    # print(y)

    currentWindow = getCurrentWindow(windows,x,y,iRank)     # get currently selected window (input cursor position and currently selected bbox area ranking)
                                            # loop through all windows and update property in window object to indicate if the cursor is inside the window
                                            # output the bbox window with index iRank and capped iRank

    dispCurrentWindow(fig, currentWindow, screen) # grey out area around the region spanned by the current window


# edit() # bring up GUI to edit tag/annotate screnshot

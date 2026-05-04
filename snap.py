import keyboard
import matplotlib as mpl
import matplotlib.pyplot as plt
import mouse
from mouse import WheelEvent
from PIL import ImageGrab
import screeninfo

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
    Scroll up decrements iRank by 1 (zoom in)
    Scroll down increments iRank by 1 (zoom out)
    """
    global iRank
    if isinstance(event, WheelEvent): # only action interactions with the scroll wheel
        if event.delta > 0:  # Scroll up, zoom in
            iRank -= 1
            print(f"iRank decremented: {iRank}")
        elif event.delta < 0:  # Scroll down, zoom out
            iRank += 1
            print(f"iRank incremented: {iRank}")

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

def isCursorInWindow(window, origin=(0,0)):
    """
    Indicate if cursor is inside the queried window.
    Args:
        window (Window): Window object.
        origin (tuple): global x,y coordinates of top-left corner of the selected screen containing the quried window.
    Returns:
        isInWindow (bool): True implies the cursor is inside the window. False implies it is outside the window.
    """
    x, y = mouse.get_position() # return current position of cursor
    # print(x)
    # print(y)

    # Convert from global coordinates to local screen coordinates
    x -= origin[0]
    y -= origin[1]

    # Check if cursor is within the window's bounding box
    if x > window.bbox[0] and x < window.bbox[2] and y > window.bbox[1] and y < window.bbox[3]:
        return True
    else:
        return False

def getCurrentWindow(windows, iRank, screenOrigin):
    """
    Return currently selected window.
    Args:
        windows (list): List of Window objects present in current screenshot.
        iRank (int): Index of windows list corresponding to current window.
        screenOrigin (tuple): Global x,y coordinates of top-left corner of the selected screen containing the windows.
    Returns:
        curr_window (Window): Current window.
    """
    windowsContainingCursor = [window for window in windows if isCursorInWindow(window, screenOrigin)] # isolate windows containing the cursor

    if len(windowsContainingCursor) == 0:
        return windows[-1] # return full screen (largest area) if cursor is not on the screen

    if iRank != 0: # prevent divide by zero error
        iRank = iRank % len(windowsContainingCursor) # wrap around to smallest bbox if number of valid windows is exceeded
    
    return windowsContainingCursor[iRank]

# Capture current screen
monitors = screeninfo.get_monitors() # get monitor dimensions
for monitor in monitors:
    screenWindow = Window( # define bounding box of monitors (left, top, right, bottom)
        (
            monitor.x,
            monitor.y,
            monitor.x + monitor.width,
            monitor.y + monitor.height
        )
    )
    if isCursorInWindow(screenWindow):
        screen = ImageGrab.grab(bbox=screenWindow.bbox, all_screens=True) # capture current screen
        # screen.show()
        break

screenOrigin = (screenWindow.x, screenWindow.y) # global coordinates of top-left corner of selected screen
windows = getWindows(screen) # output list of windows identified in current screen

windows = sorted(windows, key=lambda window: window.area) # arrange windows in order of increasing area

# Hook scroll events
mouse.hook(on_scroll) # will trigger callback on any mouse event (even moving the cursor)

# Setup interactive figure
mpl.rcParams['toolbar'] = 'None' # hide navigation toolbar in all figures
plt.ion()  # enable interactive mode
fig = plt.figure()

# Open fig on current screen
figManager = plt.get_current_fig_manager()
figManager.window.overrideredirect(True) # remove title bar (minimise, maximise, close) and borders
try:
    # Works for Qt backend
    figManager.window.setGeometry(screenWindow.x, screenWindow.y, screenWindow.dx, screenWindow.dy)
except Exception:
    try:
        # Works for TkAgg backend
        figManager.window.wm_geometry(f"{screenWindow.dx}x{screenWindow.dy}+{screenWindow.x}+{screenWindow.y}")
    except Exception as e:
        print("Could not set window position:", e)
figManager.window.update_idletasks()
fig.set_size_inches(screen.size[0] / fig.dpi, screen.size[1] / fig.dpi)
fig.subplots_adjust(left=0, right=1, top=1, bottom=0)  # remove white-space padding around axes
fig.add_axes([0, 0, 1, 1])  # ensure axes fill the entire figure
# figManager.window.state('zoomed')
# figManager.full_screen_toggle() # open figure in fullscreen mode

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

    currentWindow = getCurrentWindow(windows,iRank, screenOrigin)     # get currently selected window (input cursor position and currently selected bbox area ranking)
                                            # loop through all windows and update property in window object to indicate if the cursor is inside the window
                                            # output the bbox window with index iRank and capped iRank

    dispCurrentWindow(fig, currentWindow, screen) # grey out area around the region spanned by the current window


# edit() # bring up GUI to edit tag/annotate screnshot

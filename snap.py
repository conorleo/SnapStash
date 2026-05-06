import datetime
import threading
import time
import keyboard
import matplotlib.pyplot as plt
import mouse
import piexif # image metadata
from mouse import WheelEvent
from PIL import ImageGrab
import screeninfo

# Copy to clipboard
import win32clipboard as clip
import win32con
from io import BytesIO

from tag import collectTagsForSnap
from windows import Window, getWindows, dispCurrentWindow

capture_lock = threading.Lock()
capture_requested = threading.Event()

def buildJpegExifForWindowsTags(tags):
    """
    Build JPEG EXIF metadata for Windows Explorer "Tags".
    Args:
        tags (list[str]): User-defined image tags.
    Returns:
        bytes: EXIF bytes for JPEG save.
    """
    windowsTagString = ";".join(tags)
    # Windows stores XPKeywords as UTF-16LE with trailing null terminator.
    xpKeywords = windowsTagString.encode("utf-16le") + b"\x00\x00"
    exifDict = {
        "0th": {
            piexif.ImageIFD.XPKeywords: xpKeywords
        },
        "Exif": {},
        "GPS": {},
        "1st": {},
        "thumbnail": None
    }
    return piexif.dump(exifDict)

def on_scroll(event, rank_state):
    """
    Callback function triggered when the mouse is scrolled.
    event.delta > 0 means scroll up, event.delta < 0 means scroll down.
    Scroll up decrements iRank by 1 (zoom in)
    Scroll down increments iRank by 1 (zoom out)
    """
    if isinstance(event, WheelEvent): # only action interactions with the scroll wheel
        if event.delta > 0:  # Scroll up, zoom in
            rank_state["iRank"] -= 1
            print(f"iRank decremented: {rank_state['iRank']}")
        elif event.delta < 0:  # Scroll down, zoom out
            rank_state["iRank"] += 1
            print(f"iRank incremented: {rank_state['iRank']}")

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

def clampPointToScreen(point, screenSize):
    """
    Clamp point to valid local pixel coordinates on screen image.
    Args:
        point (tuple): (x, y) point in local screen coordinates.
        screenSize (tuple): (width, height) of screen image.
    Returns:
        tuple: clamped (x, y) point.
    """
    x = max(0, min(point[0], screenSize[0] - 1))
    y = max(0, min(point[1], screenSize[1] - 1))
    return (x, y)

def getDragBBox(start, end, screenSize):
    """
    Build crop bbox from drag start/end local coordinates.
    Returns bbox as (left, top, right, bottom) suitable for PIL crop.
    """
    # Cap bbox dimensions to screen boundaries
    start = clampPointToScreen(start, screenSize)
    end = clampPointToScreen(end, screenSize)

    left = min(start[0], end[0])
    top = min(start[1], end[1])
    right = max(start[0], end[0]) + 1
    bottom = max(start[1], end[1]) + 1
    return (left, top, right, bottom)

def getCurrentScreenCapture():
    """
    Capture and return the monitor under the cursor.
    Returns:
        tuple[Window, PIL.Image.Image] | (None, None): Screen window and image.
    """
    monitors = screeninfo.get_monitors()
    for monitor in monitors:
        screenWindow = Window(
            (
                monitor.x,
                monitor.y,
                monitor.x + monitor.width,
                monitor.y + monitor.height
            )
        )
        if isCursorInWindow(screenWindow):
            screen = ImageGrab.grab(bbox=screenWindow.bbox, all_screens=True)
            return screenWindow, screen
    return None, None

def runCaptureSession():
    """
    Run one interactive screenshot capture session.
    """
    if not capture_lock.acquire(blocking=False):
        print("Capture already in progress, ignoring hotkey.")
        return

    try:
        screenWindow, screen = getCurrentScreenCapture()
        if screenWindow is None or screen is None:
            print("No screen detected at cursor position.")
            return

        screenOrigin = (screenWindow.x, screenWindow.y)
        windows = [Window(screen.getbbox())] # fallback immediately to full-screen selection
        rank_state = {"iRank": 0}

        def detectWindowsAsync():
            nonlocal windows
            detected = getWindows(screen)
            windows = sorted(detected, key=lambda window: window.area)

        # Kick off expensive edge/contour detection without blocking startup.
        threading.Thread(target=detectWindowsAsync, daemon=True).start()

        # Hook scroll events for this session only.
        mouse.hook(lambda event: on_scroll(event, rank_state))

        # Setup interactive figure
        plt.rcParams['toolbar'] = 'None'
        plt.ion()
        fig = plt.figure()

        figManager = plt.get_current_fig_manager()
        figManager.window.overrideredirect(True)
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
        fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
        fig.add_axes([0, 0, 1, 1])

        # Keep the figure hidden until the first rendered frame is ready.
        try:
            figManager.window.withdraw()
        except Exception:
            pass

        plt.ion()

        while True:
            # ESC cancels current capture session.
            if keyboard.is_pressed("esc"):
                print("\nESC key detected. Capture cancelled.")
                break

            currentWindow = getCurrentWindow(windows, rank_state["iRank"], screenOrigin)

            # Save snap on mouse release:
            # - click -> crop selected window
            # - drag  -> crop dragged rectangle
            if mouse.is_pressed("left"):
                moveThreshold = 5
                x, y = mouse.get_position()
                dragStart = (x - screenOrigin[0], y - screenOrigin[1])
                dragEnd = dragStart

                # Click-and-drag
                while mouse.is_pressed("left"):
                    if keyboard.is_pressed("esc"):
                        print("\nESC key detected. Capture cancelled.")
                        return

                    x, y = mouse.get_position()
                    dragEnd = (x - screenOrigin[0], y - screenOrigin[1])

                    dragWindow = Window(getDragBBox(dragStart, dragEnd, screen.size))
                    dispCurrentWindow(fig, dragWindow, screen)

                isDrag = abs(dragEnd[0] - dragStart[0]) >= moveThreshold or abs(dragEnd[1] - dragStart[1]) >= moveThreshold
                if isDrag:
                    currentWindow = dragWindow

                screenshot = screen.crop(currentWindow.bbox).convert("RGB")
                tags = collectTagsForSnap(
                    screenBounds=(screenWindow.x, screenWindow.y, screenWindow.dx, screenWindow.dy)
                )
                screenshot.save(
                    f"snaps/{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.jpg",
                    "JPEG",
                    exif=buildJpegExifForWindowsTags(tags)
                )
                copyToClipboard(screenshot)
                break

            dispCurrentWindow(fig, currentWindow, screen)

    finally:
        mouse.unhook_all()
        plt.close("all")
        capture_lock.release()

def main():
    """
    Start lightweight background listener and wait for PrtScn.
    """
    print("SnapStash listener running. Press PrtScn to capture. Press Ctrl+C to exit.")
    # Swallow OS PrtScn behavior, but defer capture work to main thread.
    keyboard.on_press_key(
        "print screen",
        lambda _event: capture_requested.set(),
        suppress=True
    )

    while True:
        if capture_requested.wait(timeout=0.1):
            capture_requested.clear()
            runCaptureSession()
        time.sleep(0.01)

if __name__ == "__main__":
    main()


# edit() # bring up GUI to edit tag/annotate screnshot

import keyboard
import mouse
import time

# getScreen() # capture current screen

# getWindows() # output list of windows identified in current screen

# arrange windows in order of increasing area

iRank = 0 # index of the current selected window out of the set of windows currently containing the cursor (0 => smallest window containing the cursor will be selected)

while True:
    # Exit program if ESC key pressed
    if keyboard.is_pressed("esc"):
        print("\nESC key detected. Exiting...")
        break

    # Save snap if left-click is detected
    if mouse.is_pressed("left"):
        print("\nLeft-click detected. Exiting...")
        # crop() # crop img to region defined by current window
        # tag() # tag the img
        # save() # save the img
        break

    # Increment iRank if scroll up detected

    # Decrement iRank if scroll down detected

    # Temporarily add delay
    time.sleep(0.05)

    # getCursor() # return current position of cursor

    # getCurrentWindow(windows,x,y,iRank)   # get currently selected window (input cursor position and currently selected bbox area ranking)
                                            # loop through all windows and update property in window object to indicate if the cursor is inside the window
                                            # output the bbox window with index iRank and capped iRank

    # displayCurrentWindow() # grey out area around the region spanned by the current window


# edit() # bring up GUI to edit tag/annotate screnshot

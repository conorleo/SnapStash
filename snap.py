import keyboard
import mouse
import time

while True:
    # Exit program if ESC key pressed
    if keyboard.is_pressed("esc"):
        print("\nESC key detected. Exiting...")
        break

    # Save snap if left-click is detected
    if mouse.is_pressed("left"):
        print("\nLeft-click detected. Exiting...")
        break

    # Temporarily add delay
    time.sleep(0.05)

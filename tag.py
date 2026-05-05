import json
import os
import tkinter as tk
from tkinter import ttk

TAG_HISTORY_PATH = "snaps/tag_history.json"

def loadTagHistory(path=TAG_HISTORY_PATH):
    """
    Load saved tag history from disk.
    Args:
        path (str): path to tag history JSON file.
    Returns:
        list[str]: previously used tags, most recent first.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    return [tag.strip() for tag in data if isinstance(tag, str) and tag.strip()]

def saveTagHistory(tags, path=TAG_HISTORY_PATH):
    """
    Persist tag history to disk.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(tags, f, indent=2)

def promptForTag(previousTags, screenBounds=None):
    """
    Show a lightweight popup to choose or type a tag.
    Args:
        previousTags (list[str]): Known tag options for quick selection.
        screenBounds (tuple | None): (x, y, width, height) for preferred popup screen.
    Returns:
        str: Selected/typed tag, or empty string when cancelled/blank.
    """
    selectedTag = {"value": ""}

    root = tk.Tk()
    root.withdraw()

    popup = tk.Toplevel(root)
    popup.title("Tag Snap")
    popup.resizable(False, False)
    popup.overrideredirect(True)
    popup.attributes("-topmost", True)
    popup.configure(padx=16, pady=14)

    style = ttk.Style(popup)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style.configure("Hint.TLabel", foreground="#666666")

    container = ttk.Frame(popup)
    container.grid(row=0, column=0, sticky="nsew")

    ttk.Label(
        container,
        text="Select an existing tag or type a new one.",
        style="Hint.TLabel"
    ).grid(row=0, column=0, pady=(0, 10), sticky="w")

    combo = ttk.Combobox(container, values=previousTags, width=36)
    combo.grid(row=1, column=0, sticky="ew")
    combo.focus_set()
    if previousTags:
        combo.current(0)

    def onSubmit():
        selectedTag["value"] = combo.get().strip()
        popup.destroy()

    def onCancel():
        selectedTag["value"] = ""
        popup.destroy()

    popup.protocol("WM_DELETE_WINDOW", onCancel)

    buttonFrame = ttk.Frame(container)
    buttonFrame.grid(row=2, column=0, pady=(12, 0))
    ttk.Button(buttonFrame, text="Cancel", command=onCancel, width=12).pack(side="right", padx=(8, 0))
    ttk.Button(buttonFrame, text="Save Tag", command=onSubmit, width=12).pack(side="right")

    popup.bind("<Return>", lambda event: onSubmit())
    popup.bind("<Escape>", lambda event: onCancel())

    popup.update_idletasks()
    if screenBounds:
        screenX, screenY, screenWidth, screenHeight = screenBounds
        x = screenX + (screenWidth // 2) - (popup.winfo_width() // 2)
        y = screenY + (screenHeight // 2) - (popup.winfo_height() // 2)
    else:
        x = (popup.winfo_screenwidth() // 2) - (popup.winfo_width() // 2)
        y = (popup.winfo_screenheight() // 2) - (popup.winfo_height() // 2)
    popup.geometry(f"+{x}+{y}")

    popup.grab_set()
    root.wait_window(popup)
    root.destroy()
    return selectedTag["value"]

def collectTagsForSnap(screenBounds=None):
    """
    Prompt for a tag and return JPEG tags list.
    """
    tagHistory = loadTagHistory()
    selectedTag = promptForTag(tagHistory, screenBounds=screenBounds)

    tags = []
    if selectedTag:
        tags.append(selectedTag)

        # keep most-recent tags first and deduplicate case-insensitively
        lowerSeen = set()
        deduped = []
        for tag in [selectedTag] + tagHistory:
            key = tag.lower()
            if key not in lowerSeen:
                lowerSeen.add(key)
                deduped.append(tag)
        saveTagHistory(deduped)

    return tags

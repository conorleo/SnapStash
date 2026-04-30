import cv2
import matplotlib.pyplot as plt
import numpy as np

class Window:
    def __init__(self, bbox=(0,0,0,0)):
        self.bbox = bbox # (left, top, right, bottom), (x0, y0, x1, y1) where 0 is the top-left corner and 1 is the bottom-right corner of the bounding box
        self.area = self.calcArea() # area of the bounding box

    def calcArea(self):
        return (self.bbox[2] - self.bbox[0])*(self.bbox[3] - self.bbox[1]) # (x1 - x0)*(y1 - y0)
    

def getEdges(img, ksize=7, isDebug=False):
    """
    Detect horizontal anf vertical edges in image.
    Args:
        img (PIL.Image.Image): image in which to find edges
        ksize (int): kernel size for sobol, typically 3, 5 or 7
        isDebug (bool): set to true to plot sobel output images intended for debugging
    Returns:
        sobel (tuple): stores x and y sobel images
    """
    # Convert image to array
    img_array = np.array(img)

    # Convert to greyscale for edge detection
    gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)

    # Detect vertical edges 
    sobel_x = cv2.Sobel(gray, ddepth=cv2.CV_64F, dx=1, dy=0, ksize=ksize) # first derivative in x direction
    sobel_x = cv2.convertScaleAbs(sobel_x) # convert to absolute values (gradient can be negative)

    # Detect horizontal edges
    sobel_y = cv2.Sobel(gray, ddepth=cv2.CV_64F, dx=0, dy=1, ksize=ksize) # first derivative in y direction
    sobel_y = cv2.convertScaleAbs(sobel_y)

    if isDebug:
        plt.figure(figsize=(8, 6))
        plt.imshow(sobel_x, cmap="gray")
        plt.title("Sobel X Direction (Horizontal Edges)")
        plt.axis("off")

        plt.figure(figsize=(8, 6))
        plt.imshow(sobel_y, cmap="gray")
        plt.title("Sobel Y Direction (Vertical Edges)")
        plt.axis("off")

        plt.show()

    return (sobel_x, sobel_y)

def getWindows(img):
    """
    Args:
        img (PIL.Image.Image): image of current screen
    """
    getEdges(img, isDebug=True)
    bbox = img.getbbox() # temp return full screen bbox
    windows = [Window(bbox)]
    
    return windows

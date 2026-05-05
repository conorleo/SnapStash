import cv2
import matplotlib.pyplot as plt
import numpy as np

class Window:
    def __init__(self, bbox=(0,0,0,0)):
        self.bbox = bbox # (left, top, right, bottom), (x0, y0, x1, y1) where 0 is the top-left corner and 1 is the bottom-right corner of the bounding box
        self.x = self.bbox[0] # top-left x coordinate
        self.y = self.bbox[1] # top-left y coordinate
        self.dx = self.bbox[2] - self.bbox[0] # horizontal side length, (x1 - x0)
        self.dy = self.bbox[3] - self.bbox[1] # vertical side length, (y1 - y0)
        self.area = self.calcArea() # area of the bounding box

    def calcArea(self):
        return self.dx*self.dy
    
    def plot(self, ax=None):
        x = [
            self.bbox[0],           # top-left
            self.bbox[0] + self.dx, # top-right
            self.bbox[0] + self.dx, # bottom-right
            self.bbox[0],           # bottom-left
            self.bbox[0]            # repeat top-left
        ]
        y = [
            self.bbox[1],           # top-left
            self.bbox[1],           # top-right
            self.bbox[1] + self.dy, # bottom-right
            self.bbox[1] + self.dy, # bottom-left
            self.bbox[1]            # repeat top-left
        ]
        if ax is None:
            plt.plot(x, y)
        else:
            ax.plot(x, y)
    

def dispCurrentWindow(fig, currentWindow, img):
    """
    Grey out region around current window on-screen.
    Args:
        currentWindow (Window): Currently selected window for snipping with the cursor inside it.
    """
    rgb = np.array(img)
    gray = cv2.cvtColor(rgb, cv2.COLOR_BGR2GRAY)
    gray_rbg = np.stack((gray,)*3, axis=-1)  # make grayscale image 3-channel to accommodate later rgb addition

    # replace current window with rgb image (surrounding area grayscale)
    gray_rbg[currentWindow.bbox[1]:currentWindow.bbox[3], currentWindow.bbox[0]:currentWindow.bbox[2]] = rgb[currentWindow.bbox[1]:currentWindow.bbox[3], currentWindow.bbox[0]:currentWindow.bbox[2]]

    manager = fig.canvas.manager
    first_render = not getattr(fig, '_has_been_shown', False)

    ax = fig.gca()
    ax.clear()
    ax.axis('off')  # hide axes, ticks, and labels
    ax.set_xlim(0, gray_rbg.shape[1])
    ax.set_ylim(gray_rbg.shape[0], 0)
    ax.imshow(gray_rbg, aspect='auto', origin='upper', interpolation='nearest')
    currentWindow.plot(ax=ax) # plot bounding box perimeter

    if first_render:
        fig.canvas.draw()  # paint content before showing the window
        try:
            manager.window.deiconify()
        except Exception:
            try:
                manager.window.show()
            except Exception:
                pass
        fig._has_been_shown = True
    else:
        fig.canvas.draw_idle() # update fig

    plt.pause(0.0001) # pause to allow fig to render


def poly2Rect(poly):
    """
    Convert poly defined by four (x,y) pairs of vertices into rectangular bounding box, defined by (left, top, right, bottom) pixel locations.
    Args:
        poly (list): four (x,y) pairs of int values defining coordinates of each vertex of a polygon.
    Returns:
        bbox (tuple): four int values defining the top-left and bottom-right vertices of a rectangle, (left, top, right, bottom).
    """
    nVertices = 4
    # Separate x and y pixel coordinates
    x = [poly[i][0][0] for i in range(nVertices)]
    y = [poly[i][0][1] for i in range(nVertices)]

    bbox = (min(x), min(y), max(x), max(y))  # (left, top, right, bottom)

    return bbox

def getEdges(img, ksize=3, isDebug=False):
    """
    Detect horizontal anf vertical edges in image.
    Args:
        img (PIL.Image.Image): image in which to find edges
        ksize (int): kernel size for sobol, typically 3, 5 or 7
        isDebug (bool): set to true to plot output images intended for debugging
    Returns:
        edges (np.array): grayscale image identifying edge locations. Values assigned to each pixel. If >0, the pixel lies on an edge.
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

    edges = cv2.bitwise_xor(sobel_x, sobel_y)
    # edges = cv2.Canny(gray, 100, 150) # Canny edge detection, min and max thresholds for edges

    if isDebug:
        # plt.figure(figsize=(8, 6))
        # plt.imshow(sobel_x, cmap="gray")
        # plt.title("Sobel X Direction (Horizontal Edges)")
        # plt.axis("off")

        # plt.figure(figsize=(8, 6))
        # plt.imshow(sobel_y, cmap="gray")
        # plt.title("Sobel Y Direction (Vertical Edges)")
        # plt.axis("off")

        plt.figure(figsize=(8, 6))
        plt.imshow(edges, cmap="gray")
        plt.title("Edges")
        plt.axis("off")

        plt.show()

    return edges

def getContours(edges, img, isDebug=False):
    """
    Extract each contour from edge image.
    Args:
        edges (np.array): 0-255 for each pixel, 0 if pixel is not on an edge, up to 255 if the pixel is on an edge.
        img (PIL.Image.Image): image (for debug plotting).
        isDebug (bool): set to true to plot output images intended for debugging.
    Returns:
        contours (np.array): vertices describing continuous, closed shapes.
    """
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE) # RETR_LIST => return all contours unordered
                                                                                  # CHAIN_APPROX_SIMPLE => returns only vertices
    if isDebug:
        img_array = np.array(img)
        cv2.drawContours(img_array, contours, -1, (0, 255, 0), 3)
        cv2.imshow("Contours", img_array)

    return contours

def getBoxes(contours, img, isDebug=False):
    """
    Extract rectangles from contours.
    Args:
        contours (np.array): vertices defining continuous closed shapes.
        img (PIL.Image.Image): image (for debug plotting).
        isDebug (bool): set to true to plot output images intended for debugging.
    Returns:
        bbox (list): List of bounding boxes each storing a list of four (x,y) int pairs defining vertex locations.
    """
    bbox = []
    polys = []
    for contour in contours:
        # rectimate the contour to a polygon
        epsilon = 0.02 * cv2.arcLength(contour, True) # precision term that scales with the contour perimeter
        poly = cv2.approxPolyDP(contour, epsilon, True) # list of four (x,y) pairs defining vertex locations
                                                        # True => return only closed contours
        # Check if polygon has 4 vertices and is convex
        if len(poly) == 4 and cv2.isContourConvex(poly):
            x, y, w, h = cv2.boundingRect(poly)

            if w > 20 and h > 20:  # ignore very small shapes
                polys += [poly]
                bbox += [poly2Rect(poly)]
    
    if isDebug:
        img_array = np.array(img)
        cv2.drawContours(img_array, polys, -1, (0, 255, 0), 3)
        cv2.imshow("Contours", img_array)

    return bbox

def getWindows(img, isDebug=False):
    """
    Extract rectangular windows from screen for automatic clipping.
    Args:
        img (PIL.Image.Image): image of current screen.
        isDebug (bool): set to true to plot output images for debugging.
    Returns:
        windows (list): List of bounding boxes corresponding to clippable windows. Each bbox stores [left, top, right, bottom] pixel locations defining vertices.
    """
    edges       = getEdges(img, isDebug=isDebug)
    contours    = getContours(edges, img, isDebug=isDebug)
    bbox        = getBoxes(contours, img, isDebug=isDebug)

    bbox += [img.getbbox()] # append full screen bbox
    windows = [Window(rect) for rect in bbox] # convert each bbox to window object

    if isDebug:
        plt.figure(figsize=(8, 6))
        plt.imshow(img)
        plt.title("Windows")
        plt.axis("off")

        for window in windows:
            window.plot()
    
    return windows

if __name__ == "__main__":
    from PIL import Image

    img = Image.open("snaps/screen.png")
    getWindows(img, True)

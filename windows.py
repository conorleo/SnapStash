class Window:
    def __init__(self, bbox=(0,0,0,0)):
        self.bbox = bbox # (left, top, right, bottom), (x0, y0, x1, y1) where 0 is the top-left corner and 1 is the bottom-right corner of the bounding box
        self.area = self.calcArea() # area of the bounding box

    def calcArea(self):
        return (self.bbox[2] - self.bbox[0])*(self.bbox[3] - self.bbox[1]) # (x1 - x0)*(y1 - y0)

def getWindows(img):
    """
    Args:
        img (PIL.Image.Image): image of current screen
    """
    bbox = img.getbbox() # temp return full screen bbox
    windows = [Window(bbox)]
    
    return windows

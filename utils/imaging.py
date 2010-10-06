from PIL import Image, ImageFile
from cStringIO import StringIO
import os

# Fix to allow use of optimize in the Image save method
# Trying to avoid the error: "IOError: encoder error -2 when writing image file"
ImageFile.MAXBLOCK = 1000000 # default is 64k

def image_open(stream_or_path):
    # Open stream or file
    img = Image.open(stream_or_path)
    return img

def resize(stream_or_path, max_width=None, max_height=None, method='crop'):
    # Open stream or file
    img = image_open(stream_or_path)

    # Store original image width and height
    w, h = map(float, img.size)

    # Use the original size if no size given
    max_width, max_height = map(float, (max_width or w, max_height or h))
    
    if method == 'fit':
        # Proportinally resize
        img.thumbnail(map(int, (max_width, max_height)), Image.ANTIALIAS)
    elif method == 'crop':
        # Find the closest bigger proportion to the maximum size
        scale = max(max_width / w, max_height / h)

        # Image bigger than maximum size?
        if (scale < 1):
            # Calculate proportions and resize
            img.thumbnail(map(int, (w * scale, h * scale)), Image.ANTIALIAS)
            # Update resized dimensions
            w, h = img.size
            
        # Avoid enlarging the image
        max_width = min(max_width, w)
        max_height = min(max_height, h)

        # Define the cropping box
        left = (w - max_width) / 2
        top = (h - max_height) / 2
        right = left + max_width
        bottom = top + max_height
        
        # Crop to fit the desired size
        img = img.crop(map(int, (left, top, right, bottom)))

    return img

def resize_file(path, quality=80, save_as=None, **kwargs):
    # Open the file and resize
    img = resize(path, **kwargs)

    # Extract the extension (without the '.')
    ext = os.path.splitext(path)[1].upper()

    # Save the file
    img.save(save_as or path, quality=quality, optimize=(ext!='.GIF'))
    
    return img
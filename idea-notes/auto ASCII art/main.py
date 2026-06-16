import numpy as np
from PIL import Image, ImageFont
from tkinter import Tk, Button, Label, filedialog
import os
import msvcrt

ASCII_CHARS = "@%#*+=-:. "

def grayify(img):
    return img.convert("L")

def pixels_to_ascii(img):
    pixels = np.array(img).astype(int)
    chars = ASCII_CHARS
    idx = (pixels * len(chars) // 256)
    idx = np.clip(idx, 0, len(chars) - 1)
    return "\n".join("".join(chars[i] for i in row) for row in idx)

def convert_to_ascii_str(path, font_path="DejaVuSansMono.ttf", font_size=12, new_width=100):
    try:
        img = Image.open(path)
    except Exception as e:
        raise RuntimeError(f"Can't open image: {e}")

    try:
        font = ImageFont.truetype(font_path, font_size)
    except:
        font = ImageFont.load_default()

    bbox = font.getbbox("A")
    fw = bbox[2] - bbox[0]
    fh = bbox[3] - bbox[1]
    font_ratio = fh / fw

    orig_w, orig_h = img.size
    aspect = orig_h / orig_w
    new_height = max(1, int(aspect * new_width * font_ratio))

    resized = img.resize((new_width, new_height))
    gray = grayify(resized)
    ascii_str = pixels_to_ascii(gray)
    return ascii_str

def wait_for_q():
    print("by ulsidae")
    while True:
        if msvcrt.kbhit():
            key = msvcrt.getch()
            if key.lower() == b'q':
                break

def select_file():
    filetypes = [("Image files", "*.png *.jpg *.jpeg *.bmp *.gif"), ("All files", "*.*")]
    im_path = filedialog.askopenfilename(title="select img", filetypes=filetypes)
    if not im_path:
        root.destroy()
        return
    try:
        ascii_art = convert_to_ascii_str(im_path)

        print(ascii_art)
        wait_for_q()

        root.destroy()

    except Exception as err:
        print(f"error: {err}")
        wait_for_q()
        root.destroy()

root = Tk()
root.title("ASCII Art Converter")
root.geometry("400x150")

Label(root, text="SELECT IMAGE!").pack(padx=10, pady=20)

btn = Button(root, text="select", command=select_file, width=20)
btn.pack(pady=10)

root.mainloop()

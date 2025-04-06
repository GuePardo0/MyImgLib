from MyImgLib import *

file_path = "imagemlegal.png"
image = decode_image(file_path)
for i in image:
    print(i)
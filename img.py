import cv2
from natsort import natsorted
import os

def count_jpg_files(directory_path):
    jpg_files = [filename for filename in os.listdir(directory_path) if filename.lower().endswith(".jpg")]
    return jpg_files

def delete_images(directory_path, image_files):
    sorted_images = natsorted(image_files)
    return sorted_images

cd = os.getcwd()
cd = os.path.join(cd, 'img')
while True:
    jpg_files = count_jpg_files(cd)
    sorted_images = delete_images(cd, jpg_files)
    try:
        img = sorted_images[-2]
        img = os.path.join(cd, img)
        img = cv2.imread(img)
        cv2.imshow('RTV', img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    except IndexError:
        pass

cv2.destroyAllWindows()

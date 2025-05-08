import hashlib
import json
import os.path
import sys
from PIL import Image, TiffImagePlugin
from PIL.ExifTags import TAGS, GPSTAGS

# constants
MAX_WIDTH = 1920
MAX_HEIGHT = 1080
BASE_DIRECTORY = './'
IMAGE_GPSDATA = 34853  # GPSInfo
IMAGE_EXIFDATA = 34665  # ExifOffset


def getExifTagName(tagId) -> str:
    ''' Resolve EXIF TagIds to their Name '''
    for key, value in TAGS.items():
        if tagId == key:
            return value
    return ""


def getGPSTagName(tagId) -> str:
    ''' Resolve GPS TagIds to their Name '''
    for key, value in GPSTAGS.items():
        if tagId == key:
            return value
    return ""


def jsonable(i) -> any:
    ''' Workaround to EXIF types not being proper to json library '''
    if isinstance(i, TiffImagePlugin.IFDRational):
        i = float(i)
    elif isinstance(i, tuple):
        i = tuple(float(t) if isinstance(
            t, TiffImagePlugin.IFDRational) else t for t in i)
    elif isinstance(i, bytes):
        i = i.decode(errors="replace")
    return i


# parameters
if len(sys.argv) == 1:
    print("parameter 1 needs to be an image file")
    quit()
input_filename = sys.argv[1]
if not os.path.isfile(input_filename):
    print(f"File {input_filename} does not exist")
    quit()

# Load image
try:
    src_image = Image.open(input_filename)
    src_image_width, src_image_height = src_image.size
except:
    print(f"{input_filename} is not a readable image")
    quit()

# get sha1 hash of valid image
f = open(input_filename, "rb")
digest = hashlib.file_digest(f, "sha1")
hash = digest.hexdigest()

dst_dir_name = os.path.join(BASE_DIRECTORY, hash[0:3], hash[3:5])
dst_image_filename = os.path.join(dst_dir_name, hash + ".jpg")
dst_json_filename = os.path.join(dst_dir_name, hash + ".json")
# see if we need to resize
dst_image_width = src_image_width
dst_image_height = src_image_height
if MAX_WIDTH < dst_image_width:
    ratio = dst_image_height / dst_image_width
    dst_image_width = MAX_WIDTH
    dst_image_height = int(MAX_WIDTH * ratio)

if MAX_HEIGHT < dst_image_height:
    ratio = dst_image_width / dst_image_height
    dst_image_height = MAX_HEIGHT
    dst_image_width = int(MAX_HEIGHT * ratio)

# Create directory structure if it doesn't already exist
try:
    os.makedirs(dst_dir_name)
except:
    pass

# resize and write new image
dst_image = src_image.resize((dst_image_width, dst_image_height))
dst_image.save(dst_image_filename, "JPEG")

# Get EXIF data to store as a json file with the image
image_data = {}
exif = src_image.getexif()
if len(exif) > 0:
    for key, value in exif.items():
        if key == IMAGE_GPSDATA or key == IMAGE_EXIFDATA:
            if key == IMAGE_GPSDATA:
                gps_info = exif.get_ifd(IMAGE_GPSDATA)
                for gps_key, gps_value in gps_info.items():
                    gps_value = jsonable(gps_value)
                    tag_name = getGPSTagName(gps_key)
                    image_data.update({f"gps:{tag_name}": gps_value})
            if key == IMAGE_EXIFDATA:
                exif_info = exif.get_ifd(IMAGE_EXIFDATA)
                for exif_key, exif_value in exif_info.items():
                    exif_value = jsonable(exif_value)
                    tag_name = getExifTagName(exif_key)
                    image_data.update({f"exif:{tag_name}": exif_value})
        else:
            value = jsonable(value)
            tag_name = getExifTagName(key)
            image_data.update({f"image:{tag_name}": value})

# Write json data as hash.json
with open(dst_json_filename, "w") as json_file:
    json_file.write(json.dumps(image_data, sort_keys=True))
    json_file.close()

quit()

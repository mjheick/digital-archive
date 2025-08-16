import datetime
import hashlib
import json
import mysql.connector # pip install mysql-connector-python
import os
import subprocess
import sys
from PIL import Image, TiffImagePlugin # pip install pillow
from PIL.ExifTags import TAGS, GPSTAGS

# Acceptable mime-types for scanner based on file extension
# https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/MIME_types/Common_types
MIME_TYPES = {
  'jpeg': 'image/jpeg',
  'jpg': 'image/jpeg',
  'png': 'image/png',
  'gif': 'image/gif',
  'mpg': 'video/mpeg',
  'mpeg': 'video/mpeg',
  'mp4': 'video/mp4',
  'avi': 'video/x-msvideo',
}

# Load config
if not os.path.isfile("config.json"):
    print("configuration does not exist")
    sys.exit(1)
with open('config.json') as file:
  config = json.load(file)

# Constants
THUMBNAIL_BASEFOLDER = os.path.join(config["thumbnail_basefolder"], config["thumbnail_folder"])
THUMBNAIL_DIMENSIONS = (config["thumbnail_dimensions"][0], config["thumbnail_dimensions"][1])
FFPROBE_EXEC = config["ffprobe_exec"]
FFMPEG_EXEC = config["ffmpeg_exec"]
IMAGE_GPSDATA = 34853  # GPSInfo
IMAGE_EXIFDATA = 34665  # ExifOffset
SQL = {
  'host': config['database']['hostname'],
  'user': config['database']['username'],
  'password': config['database']['password'],
  'database': config['database']['database'],
}

def main():
  if len(sys.argv) != 2:
    print("Need 1 parameter for base file path to use for recursive scanning")
    return 1
  if not os.path.isfile(FFPROBE_EXEC):
    print(f"ffprobe not located at {FFPROBE_EXEC}")
    return 1
  if not os.path.isfile(FFMPEG_EXEC):
    print(f"ffmpeg not located at {FFMPEG_EXEC}")
    return 1
  if not os.path.isdir(THUMBNAIL_BASEFOLDER):
    print(f"thumbnail folder at {THUMBNAIL_BASEFOLDER} is not reachable")
  
  basepath = sys.argv[1]
  
  if not os.path.isdir(basepath):
    print(f"{basepath} is not a directory")
    return 0
  
  # connect with database
  try:
    db = mysql.connector.connect(**SQL)
  except mysql.connector.errors.DatabaseError:
    print("There was an error connecting with the database. Check config")
    return 1
    
  cursor = db.cursor()
  
  # Recursively scan for all directories and files
  all_files = recursiveFolderScan(basepath)
  print(f"Files found: " + str(len(all_files)))
  
  # Loop through all_files, get filename, filesize, filedate
  for file in all_files:
    filename = os.path.basename(file)
    filesize = os.path.getsize(file)
    filepath = os.path.dirname(file)
    filetype = getMimeType(file)
    filedate = str(datetime.datetime.fromtimestamp(os.path.getmtime(file)))
    filedate = filedate[0:19]
    
    # does this entry exist in the database?
    cursor.execute(
      "SELECT * FROM entries WHERE filename=%s AND filepath=%s AND filesize=%s and filetype=%s and filedate=%s LIMIT 1",
      (filename, filepath, filesize, filetype, filedate)
    )
    result = cursor.fetchall()
    if not result:
      print(f"{filename} does not exist in database ({filesize}, {filetype}, {filedate})")
      hash = fileSha256(file)
      metadata = json.dumps(getMetadata(file), sort_keys=True)
      cursor.execute(
        "INSERT INTO entries (hash, filename, filepath, filesize, filetype, filedate, filemetadata) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (hash, filename, filepath, filesize, filetype, filedate, metadata)
      )
      db.commit()
      makeThumbnail(file, hash)
    else:
      print(f"{filename} exists")
      pass
  # Wrap things up
  cursor.close()
  db.close()

def recursiveFolderScan(basepath:str):
  our_files = []
  other_files = []
  contents = os.listdir(basepath)
  # For any directories in this list we need to recursively scan them and return the files
  for entry in contents:
    subentry = os.path.join(basepath, entry)
    if os.path.isdir(subentry):
      other_files = recursiveFolderScan(subentry)
      our_files = our_files + other_files
    if os.path.isfile(subentry):
      if acceptableMimeType(subentry):
        our_files.append(subentry)
  return our_files

def acceptableMimeType(filename:str):
  for extension in MIME_TYPES:
    if filename.lower().endswith("." + extension):
      return True
  return False    

def getMimeType(filename:str):
  for extension in MIME_TYPES:
    if filename.lower().endswith("." + extension):
      return MIME_TYPES[extension]

def fileSha256(filename:str):
  sha256_hash = hashlib.sha256()
  with open(filename,"rb") as f:
    for byte_block in iter(lambda: f.read(8192), b""):
      sha256_hash.update(byte_block)
  return sha256_hash.hexdigest()

def getMetadata(filename:str):
  metadata = {}
  mime = getMimeType(filename)
  if mime.find("image/") != -1:
    try:
      image = Image.open(filename)
      try:
        exifdata = image.getexif()
      except OSError:
        exifdata = {}
      for key, value in exifdata.items():
        if key == IMAGE_GPSDATA:
          gps_info = exifdata.get_ifd(IMAGE_GPSDATA)
          for gps_key, gps_value in gps_info.items():
            gps_value = jsonable(gps_value)
            tag_name = getGPSTagName(gps_key)
            metadata[tag_name] = gps_value
        elif key == IMAGE_EXIFDATA:
          exif_info = exifdata.get_ifd(IMAGE_EXIFDATA)
          for exif_key, exif_value in exif_info.items():
            exif_value = jsonable(exif_value)
            tag_name = getExifTagName(exif_key)
            metadata[tag_name] = exif_value
        else:
          value = jsonable(value)
          tag_name = getExifTagName(key)
          metadata[tag_name] = value
    except (Image.UnidentifiedImageError, OSError):
      pass
  if mime.find("video/") != -1:
    proc = subprocess.run([FFPROBE_EXEC, "-hide_banner", "-loglevel", "fatal", "-show_error", "-show_format", "-show_streams", "-show_programs", "-show_chapters", "-show_private_data", "-print_format", "json", filename], capture_output=True)
    output = proc.stdout
    metadata = json.loads(output)
  return metadata

def getExifTagName(tagId) -> str:
  for key, value in TAGS.items():
    if tagId == key:
      return value
  return ""

def getGPSTagName(tagId) -> str:
  for key, value in GPSTAGS.items():
    if tagId == key:
      return value
  return ""

def jsonable(i) -> any:
  if isinstance(i, TiffImagePlugin.IFDRational):
    try:
      i = float(i)
    except ZeroDivisionError:
      i = 0
  elif isinstance(i, tuple):
    try:
      i = tuple(float(t) if isinstance(t, TiffImagePlugin.IFDRational) else t for t in i)
    except ZeroDivisionError:
      i = 0
  elif isinstance(i, bytes):
    i = i.decode(errors="replace")
  return i

def convert_to_degrees(value):
  d = float(value[0])
  m = float(value[1])
  s = float(value[2])
  return d + (m / 60.0) + (s / 3600.0)

def get_gps_info(exif_data):
  gps_info = {}
  if "GPSInfo" in exif_data:
    for key, val in exif_data["GPSInfo"].items():
      decoded = GPSTAGS.get(key, key)
      gps_info[decoded] = val
  if "GPSLatitude" in gps_info and "GPSLatitudeRef" in gps_info and "GPSLongitude" in gps_info and "GPSLongitudeRef" in gps_info:
    lat = convert_to_degrees(gps_info["GPSLatitude"])
    if gps_info["GPSLatitudeRef"] != "N":
      lat = -lat
    lon = convert_to_degrees(gps_info["GPSLongitude"])
    if gps_info["GPSLongitudeRef"] != "E":
      lon = -lon
    gps_info["latitude"] = lat
    gps_info["longitude"] = lon
  return gps_info

def makeThumbnail(filename:str, hash:str):
  # TODO: need default image for unknowns, possibly just symlinking to it so it changes one->all
  output_filename = os.path.join(THUMBNAIL_BASEFOLDER, hash[0:7] + ".jpg")
  if os.path.isfile(output_filename):
    return
  mime = getMimeType(filename)
  tn_width = THUMBNAIL_DIMENSIONS[0]
  tn_height = THUMBNAIL_DIMENSIONS[1]
  if mime.find("image/") != -1:
    try:
      image = Image.open(filename)
      image_width, image_height = image.size
      # Do math to resise this down to THUMBNAIL_DIMENSIONS
      if tn_width < image_width:
        ratio = image_height / image_width
        tn_height = int(tn_width * ratio)
      if tn_height < image_height:
        ratio = image_width / image_height
        tn_width = int(tn_height * ratio)
      if tn_width == 0 or tn_height == 0:
        tn_width = THUMBNAIL_DIMENSIONS[0]
        tn_height = THUMBNAIL_DIMENSIONS[1]
      # tn_* dimensions are now set
      tn_image = image.resize((tn_width, tn_height))
      tn_image.save(output_filename, "JPEG")
    except (Image.UnidentifiedImageError, OSError, SyntaxError):
      pass
  elif mime.find("video/") != -1:
    tmp_filename = os.path.join(THUMBNAIL_BASEFOLDER, hash + ".jpg")
    subprocess.run([FFMPEG_EXEC, "-ss", "00:00:00", "-i", filename, "-frames:v", "1", tmp_filename], capture_output=True)
    try:
      # copy/paste of image resize from above
      image = Image.open(tmp_filename)
      image_width, image_height = image.size
      # Do math to resise this down to THUMBNAIL_DIMENSIONS
      if tn_width < image_width:
        ratio = image_height / image_width
        tn_height = int(tn_width * ratio)
      if tn_height < image_height:
        ratio = image_width / image_height
        tn_width = int(tn_height * ratio)
      if tn_width == 0 or tn_height == 0:
        tn_width = THUMBNAIL_DIMENSIONS[0]
        tn_height = THUMBNAIL_DIMENSIONS[1]
      # tn_* dimensions are now set
      tn_image = image.resize((tn_width, tn_height))
      tn_image.save(output_filename, "JPEG")
      os.remove(tmp_filename)
    except (Image.UnidentifiedImageError, OSError, SyntaxError):
      pass
  else:
    pass
  return

main()

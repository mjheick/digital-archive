import datetime
import hashlib
import json
import mysql.connector # pip install mysql-connector-python
import os
import subprocess
import sys
from PIL import Image, TiffImagePlugin # pip install pillow
from PIL.ExifTags import TAGS, GPSTAGS

thumbnail_basefolder = '/tmp/'
thumbnail_dimensions = (400, 400)
ffprobe_exec = '/bin/ffprobe'
ffmpeg_exec = '/bin/ffmpeg'
IMAGE_GPSDATA = 34853  # GPSInfo
IMAGE_EXIFDATA = 34665  # ExifOffset

# Acceptable mime-types for scanner based on file extension
# https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/MIME_types/Common_types
mime_types = {
  'jpeg': 'image/jpeg',
  'jpg': 'image/jpeg',
  'png': 'image/png',
  'gif': 'image/gif',
  'mpg': 'video/mpeg',
  'mpeg': 'video/mpeg',
  #'mp3': 'audio/mpeg',
  'mp4': 'video/mp4',
  'avi': 'video/x-msvideo',
}

sql = {
  'host': 'localhost',
  'username': 'digital_archive',
  'password': 'digital_archive',
  'database': 'digital_archive'
}

def main():
  if len(sys.argv) != 2:
    print("Need 1 parameter for base file path to use for recursive scanning")
    return 1
  if not os.path.isfile(ffprobe_exec):
    print(f"ffprobe not located at {ffprobe_exec}")
    return 1
  if not os.path.isfile(ffmpeg_exec):
    print(f"ffmpeg not located at {ffmpeg_exec}")
    return 1
  if not os.path.isdir(thumbnail_basefolder):
    print(f"thumbnail folder at {thumbnail_basefolder} is not reachable")
    

  basepath = sys.argv[1]
    
  if not os.path.isdir(basepath):
    print(f"{basepath} is not a directory")
    return 0
  
  # connect with database
  db = mysql.connector.connect(host=sql["host"], user=sql["username"], password=sql["password"], database=sql["database"])
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
    filedate = datetime.datetime.fromtimestamp(os.path.getmtime(file))
    
    # does this entry exist in the database?
    cursor.execute(
      "SELECT * FROM entries WHERE filename=%s AND filepath=%s AND filesize=%s and filetype=%s and filedate=%s LIMIT 1",
      (filename, filepath, filesize, filetype, filedate)
    )
    result = cursor.fetchall()
    if len(result) == 0:
      print(f"{filename} does not exist in database ({filesize}, {filetype}, {filedate})")
      hash = fileSha256(file)
      metadata = json.dumps(getMetadata(file), sort_keys=True)
      cursor.execute(
        "INSERT INTO entries (hash, filename, filepath, filesize, filetype, filedate, filemetadata) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (hash, filename, filepath, filesize, filetype, filedate, metadata)
      )
      db.commit()
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
  for extension in mime_types:
    if filename.lower().endswith("." + extension):
      return True
  return False    

def getMimeType(filename:str):
  for extension in mime_types:
    if filename.lower().endswith("." + extension):
      return mime_types[extension]

def fileSha256(filename:str):
  sha256_hash = hashlib.sha256()
  with open(filename,"rb") as f:
    # Read and update hash string value in blocks of 4K
    for byte_block in iter(lambda: f.read(4096), b""):
      sha256_hash.update(byte_block)
  return sha256_hash.hexdigest()

def getMetadata(filename:str):
  metadata = {}
  mime = getMimeType(filename)
  if mime.find("image/") >= 0:
    try:
      image = Image.open(filename)
      exifdata = image.getexif()
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
    except Image.UnidentifiedImageError:
      pass
  if mime.find("video/") >= 0:
    proc = subprocess.run([ffprobe_exec, "-hide_banner", "-loglevel", "fatal", "-show_error", "-show_format", "-show_streams", "-show_programs", "-show_chapters", "-show_private_data", "-print_format", "json", filename], capture_output=True)
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

def makeThumbnail(filename:str):
  pass

main()

exit
  
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

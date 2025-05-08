import ffmpeg
import hashlib
import json
import os.path
import sys

# constants
MAX_WIDTH = 720
MAX_HEIGHT = 720
BASE_DIRECTORY = './'

# parameters
if len(sys.argv) == 1:
    print("parameter 1 needs to be a video file")
    quit()
input_filename = sys.argv[1]
if not os.path.isfile(input_filename):
    print(f"File {input_filename} does not exist")
    quit()

# Load video
try:
    vid = ffmpeg.probe(input_filename)
except:
    print(f"{input_filename} is not a readable video")
    quit()

print(vid)
quit()

# get sha1 hash of valid video
f = open(input_filename, "rb")
digest = hashlib.file_digest(f, "sha1")
hash = digest.hexdigest()

dst_dir_name = os.path.join(BASE_DIRECTORY, hash[0:3], hash[3:5])
dst_video_filename = os.path.join(dst_dir_name, hash + ".mp4")
dst_json_filename = os.path.join(dst_dir_name, hash + ".json")

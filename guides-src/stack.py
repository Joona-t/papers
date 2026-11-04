import sys
from PIL import Image
ims = [Image.open(f) for f in sys.argv[2:]]
W = max(i.width for i in ims); H = sum(i.height + 8 for i in ims)
c = Image.new('RGB', (W, H), 'white'); y = 0
for i in ims: c.paste(i, (0, y)); y += i.height + 8
c.save(sys.argv[1])

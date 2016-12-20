import os
import sys
from PIL import Image

auto = False
quiet = False
for arg in sys.argv:
	if "-a" in arg or "auto" in arg:
		auto = True
	if "-q" in arg or "quiet" in arg:
		quiet = True

for root, subs, names in os.walk("."):
	if root != ".":
		for name in names:
			if name[-4:] == ".png":
				full = os.path.join(root, name)
				handle = 0
				f = open(full, "rb")
				try:
					handle = Image.open(f)
				except (IOError, ValueError) as e:
					f.close()
					if not quiet:
						print "Image " + full + " unstable:"
						print str(e)
						if not auto:
							wait = raw_input("Delete? (Y/a/n) ")
							if "a" in wait.lower():
								auto = True
							elif "n" in wait.lower():
								continue
					os.remove(full)

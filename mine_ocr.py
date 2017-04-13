import os
import argparse
import re
import random

from PIL import Image
#import pyocr
import pytesseract


parser = argparse.ArgumentParser(description="Store OCR recognized on images of a subreddit for training usage.")
parser.add_argument("subreddit", metavar="sub", help="Subreddit to perform OCR on.")
parser.add_argument("--val_set", "-s", metavar="type", choices=["train", "test", "both"], default="both", help="Test or train. Defaults both.")
parser.add_argument("--number", "-n", dest="count", type=int, default=-1, help="Number of total images to include in visualization. Defaults to performing on all images.")
args = parser.parse_args()

unsupported = r'~'
delim = "@!@"

# Train and/or test
types = []
if args.val_set == "both":
	types.append("test")
	types.append("train")
else:
	types.append(args.val_set)
if args.count != -1:
	files = random.sample(files, args.count)
for val_type in types:
	output_folder = "ocr/" + val_type + "/"
	output = open(output_folder + args.subreddit + ".txt", "w")
	folder = args.subreddit + "/" + val_type + "/"
	files = os.listdir(folder)
	for filename in files:
		if filename[-4:] == ".png":
			print filename
			relative_path = folder + filename
			image = Image.open(relative_path)
			#text = tool.image_to_string(image, lang=lang, builder=builder)
			text = pytesseract.image_to_string(image, lang="eng")
			printable_text = re.sub(r'[^\x0a-\x7d]', unsupported, text)
			try:
				print printable_text
			except UnicodeEncodeError, e:
				print "Unsupported character:"
				print str(e)
			output.write(printable_text)
			output.write(delim)
	output.close()


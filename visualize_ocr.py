import os
import argparse
import re
import random

from PIL import Image
#import pyocr
import pytesseract


parser = argparse.ArgumentParser(description="Display OCR recognized on a few images of a subreddit.")
parser.add_argument("subreddit", metavar="pos", help="Subreddit to perform OCR on.")
parser.add_argument("--number", "-n", dest="count", type=int, default=-1, help="Number of total images to include in visualization. Defaults to infinite.")
args = parser.parse_args()

#tools = pyocr.get_available_tools()
#if len(tools) == 0:
#	print "Error: Fatal: No OCR tool found"
#	exit(1)
#tool = tools[0]
#print "Using OCR tool " + tool.get_name()
#langs = tool.get_available_languages()
#lang = "eng"
#print "Using langage " + lang

#builder = pyocr.builders.TextBuilder()
#builder.tesseract_configs.extend(("-language_model_penalty_non_freq_dict_word", "0.6",
#	"-language_model_penalty_non_dict_word", "0.8"))
#print builder.tesseract_configs

sample = open("sample.html", "w")
sample.write("<!doctype html><html><body>")

# Alternating positive/negative for early stopping
test_dir = args.subreddit + "/test/"
files = os.listdir(test_dir)
if args.count != -1:
	files = random.sample(files, args.count)
for filename in files:
	if filename[-4:] == ".png":
		print filename
		relative_path = test_dir + filename
		image = Image.open(relative_path)
		#text = tool.image_to_string(image, lang=lang, builder=builder)
		text = pytesseract.image_to_string(image, lang="eng")
		printable_text = re.sub(r'[^\x00-\x7f]',r'~', text)
		try:
			print printable_text
		except UnicodeEncodeError, e:
			print "Unsupported character:"
			print str(e)
		full_path = os.path.dirname(os.path.realpath(__file__)) + "/" + relative_path
		sample.write('<img src="' + full_path + '" /><p>' + printable_text + '</p><br /><br />')
	
sample.write("</body></html>")
sample.close()

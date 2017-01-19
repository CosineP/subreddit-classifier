import os
import argparse
import re
import random

from PIL import Image
import pyocr


parser = argparse.ArgumentParser(description="Train and save a model based on the training data.")
parser.add_argument("positive", metavar="pos", help="The subreddit to classify as >0.5.")
parser.add_argument("negative", nargs="?", metavar="neg", default="all", help="The subreddit to classify as <0.5 (default all).")
parser.add_argument("--number", "-n", dest="count", type=int, default=-2, help="Number of total images to classify.")
# parser.add_argument("--epochs", "-e", type=int, default=64, help="Number of times to iterate through the entire training set.")
# parser.add_argument("--early-stopping", dest="stop", action="store_true", help="Whether or not to stop training when test loss stops decreasing.")
# parser.add_argument("--batch-size", "-b", dest="batch_size", type=int, default=32, help="Number of images to train on at a time (more memory but better training).")
# parser.add_argument("--visualize", "-v", action="store_true", help="Post results to server running hualos on localhost:9000.")
# parser.add_argument("--treat-categorical", "-c", dest="treat_categorical", action="store_true", help="Train as a categorical classification with two classes instead of binary.")
# parser.add_argument("--weight", "-w", action="store", default=None, help="Automatically determine appropriate weights for unbalanced class sizes.")
# parser.add_argument("--no-save", "-n", dest="save", action="store_false", help="Do not save model (use for testing only!).")
args = parser.parse_args()

tools = pyocr.get_available_tools()
if len(tools) == 0:
	print "Error: Fatal: No OCR tool found"
	exit(1)
tool = tools[0]
print "Using OCR tool " + tool.get_name()
langs = tool.get_available_languages()
lang = "eng"
print "Using langage " + lang

builder = pyocr.builders.TextBuilder()
builder.tesseract_configs.extend(("-language_model_penalty_non_freq_dict_word", "0.6",
	"-language_model_penalty_non_dict_word", "0.8"))
print builder.tesseract_configs

sample = open("sample.html", "w")
sample.write("<!doctype html><html><body>")

# Alternating positive/negative for early stopping
file_pairs = zip(random.sample(os.listdir(args.negative + "/test"), args.count/2), random.sample(os.listdir(args.positive + "/test"), args.count/2))
for pair in file_pairs:
	for is_positive in range(2):
		filename = pair[is_positive]
		class_name = [args.negative, args.positive][is_positive]
		if filename[-4:] == ".png":
			print class_name + ": " + filename
			relative_path = class_name + "/test/" + filename
			image = Image.open(relative_path)
			text = tool.image_to_string(image, lang=lang, builder=builder)
			printable_text = re.sub(r'[^\x00-\x7f]',r'~', text)
			try:
				print printable_text
			except UnicodeEncodeError, e:
				print "Unsupported character:"
				print str(e)
			full_path = os.path.dirname(os.path.realpath(__file__)) + "/" + class_name + "/test/" + filename
			sample.write('<img src="' + full_path + '" /><p>' + printable_text + '</p><br /><br />')
	
sample.write("</body></html>")

import os
import argparse

from keras.models import model_from_json
from keras.preprocessing.image import load_img, img_to_array
from keras import backend as K
import numpy

K.set_image_dim_ordering('th')

parser = argparse.ArgumentParser(description="Classify test data and copy into folders of identified classes.")
parser.add_argument("positive", metavar="pos", help="The subreddit to classify as >0.5.")
parser.add_argument("negative", nargs="?", metavar="neg", default="all", help="The subreddit to classify as <0.5 (default all).")
parser.add_argument("name", nargs="?", metavar="name", help="Override default naming scheme to specify weights/json file (sans extension).")
parser.add_argument("--number", "-n", dest="count", type=int, default=-2, help="Number of total images to classify.")
parser.add_argument("--overwrite", "-o", dest="overwrite", action="store_true", help="Delete images from previous visualize_classification runs")
parser.add_argument("--resample", "-r", action="store_true", help="Use bilinear antialiasing when resizing images.")
parser.add_argument("--threshold", "-t", type=int, default=0.5, help="Use bilinear antialiasing when resizing images.")
parser.add_argument("--size", "-s", nargs=2, type=int, default=(200, 200), help="Size to resize images to, ONLY FOR CLASSIFICATION.")
parser.add_argument("--false-only", "-f", dest="false_only", action="store_true", help="Only save/visualize false positives or false negatives.")
arg = parser.parse_args()
# auto = False
# quiet = False
# for arg in sys.argv:
# 	if "-a" in arg or "auto" in arg:
# 		auto = True
# 	if "-q" in arg or "quiet" in arg:
# 		quiet = True
if not arg.name:
	arg.name = arg.positive + ("-" + arg.negative) * (arg.negative != "all")

file = open("models/" + arg.name + ".json")
model = model_from_json(file.read())
file.close()
model.load_weights("models/" + arg.name + ".h5")

if not os.path.exists("visualize"):
	os.mkdir("visualize")
for folder in [arg.negative, arg.positive]:
	if arg.overwrite and os.path.exists("visualize/" + folder):
		os.remove("visualize/" + folder)
	if not os.path.exists("visualize/" + folder):
		os.mkdir("visualize/" + folder)

# Alternating positive/negative for early stopping
file_pairs = zip(os.listdir(arg.negative + "/test")[:arg.count/2], os.listdir(arg.positive + "/test")[:arg.count/2])
for pair in file_pairs:
	for is_positive in range(2):
		filename = pair[is_positive]
		class_name = [arg.negative, arg.positive][is_positive]
		if filename[-4:] == ".png":
			print class_name + ": " + filename
			image = load_img(class_name + "/test/" + filename)
			resized_image = image.resize(arg.size)
			data = numpy.array([img_to_array(resized_image)]) / 255.
			prediction = model.predict(data)[0][-1] > arg.threshold # Prediction. Second value if categorical
			classified_as = [arg.negative, arg.positive][int(prediction)]
			if not arg.false_only or classified_as != class_name:
				image.save("visualize/" + classified_as + "/" + class_name + "-" + filename)

import os
import sys
import time
import random

from keras.models import model_from_json
from keras.preprocessing.image import load_img, img_to_array
from keras import backend as K
import numpy

from PIL import Image
from StringIO import StringIO

K.set_image_dim_ordering('th')

width = 200
height = 200
resample = True

min_width = 100
min_height = 100

top_subreddits = 1

# subreddits[False] are negatives
# subreddits[True] are positives
# aka subreddits[isPositive] gives list of subs
browse_subreddits = [
	"all"
	# ["animewallpaper"],
	# ["the_pack"],
	# ["me_irl", "meirl"]
]
post_on_match = ["animewallpaper"]
models = []
for group in post_on_match:
	file = open(group + "-last-train.json")
	model = model_from_json(file.read())
	file.close()
	model.load_weights(group + "-last-train.h5")
	models.append(model)
# exclude = ["anime_irl"] # Don't include in negative but not a positive

exts = [".jpg", ".png", "jpeg"]

if post_on_match[0] == "me_irl":
	message = "Me too thanks"
else:
	message = "/r/" + post_on_match[0]
message += "[.](http://cosinegaming.com/subreddit-classifier)"

def get_time():
	return time.strftime("%X     ", time.localtime())

def log(text):
	if not silent:
		try:
			print get_time() + str(text)
		except UnicodeEncodeError:
			print get_time() + "(Message cannot display)"

r = praw.Reddit(user_agent="Yells at people in /r/me_irl (or possibly later other subs) when they post something that would better fit in /r/the_pack based on a machine learning algorithm.",
	client_id="n7XUOradJ65e1w", client_secret="-GSs42J76X4n6rvAjE8L1k3oJR4",
	username="the_pack-bot", password="ek5H6CBmXw")

force = False
silent = False
retrain = False
scan = []
if len(sys.argv) > 1:
	for arg in sys.argv[1:]:
		if arg == "-s" or "--silent" in arg: # --silent or -s but not --scan-
			silent = True
		if "-t" in arg: # --top
			scan.append("top")
		if "-h" in arg: # --hot
			scan.append("hot")
		if "-d" in arg: #--day
			scan.append("day")
		if "-n" in arg: #--new (default)
			scan.append("new")
		if "-f" in arg: # --force
			log("Re-downloading all pictures.")
			force = True
		if "-r" in arg: # --retrain
			log("Re-training from new data after downloading.")
			retrain = True

if len(scan) == 0:
	# Default scan top of day
	scan.append("new")

gotten = 0

for scan_type in scan:

	for subreddit_name in browse_subreddits:

		subreddit = r.subreddit(subreddit_name)

		log("Retrieving from /r/" + subreddit_name + "...")

		sub_gotten = 0

		failed = False

		submissions = []
		if scan_type == "top":
			submissions = subreddit.top(limit=1000)
			log("Scanning all top posts.")
		elif scan_type == "hot":
			submissions = subreddit.hot(limit=1000)
			log("Scanning all hot posts.")
		elif scan_type == "day":
			submissions = subreddit.top("day", limit=1000)
			log("Scanning top posts of today.")
		else:
			if scan_type != "new":
				log("ERROR: Invalid scan type. Proceeding with --new.")
			submissions = subreddit.new(limit=1000)
			log("Scanning all new posts.")

		for sub in submissions:

			file = sub.url.split("/")[-1]

			if file[-4:] in exts:

				raw = False
				try:
					link = requests.get(sub.url)
					raw = link.content
				except:
					log("Unable to access an image.")
					continue

				image = False
				try:
					# image = Image.open(StringIO(raw))
					image = load_img(StringIO(raw))
				except Exception, e:
					log("Unable to process an image:")
					log(e)
					continue

				if image:

					if (browse_subreddits[0] == "all" and len(browse_subreddits) < top_subreddits
						and not str(sub.subreddit) in browse_subreddits):
						log("Adding subreddit found on /r/all: " + str(sub.subreddit))
						browse_subreddits.append(str(sub.subreddit))

					gotten += 1
					sub_gotten += 1

					if (subreddit_name == "all"):
						log(sub.subreddit)
					log(sub.title[:60])
					log(sub.url)

					image = image.resize((width, height), Image.ANTIALIAS * resample)
					data = numpy.array([img_to_array(image)])

					for model in models:
						prediction = model.predict(data)[0][0]
						log(prediction)
						if (prediction < 0.5):
							log("AAAAAAAAAAAAAAAAAAAAA")

					log("---------------")

		if not failed:
			log("Retrieved " + str(sub_gotten) + " posts from /r/" + subreddit_name + ".")
		log("------------------------------------------")

log("Retrieved " + str(gotten) + " posts total.")

if retrain:
	log("Retraining with new dataset")
	os.system("learn_data.py")
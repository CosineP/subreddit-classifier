import itertools
import os
import PIL
import praw
import requests
from BeautifulSoup import BeautifulSoup
import sys
import time
from PIL import Image
from StringIO import StringIO
import random


max_size = [768, 768]
resample = True

min_size = (162, 82) # Imgur error is 161x81

already_threshold = 8
top_subreddits = 2

# subreddits[False] are negatives
# subreddits[True] are positives
# aka subreddits[isPositive] gives list of subs
subreddits = [
	# Negatives
	["all"],
	# Positives:
	["animewallpaper"],
	["the_pack"],
	["me_irl", "meirl"],
	["catpictures", "cats"],
	["dogpictures", "lookatmydog"],
	["anime_irl"]
]
exclude = ["anime_irl", "meow_irl"] # Don't include in negative but not a positive

exts = [".jpg", ".png", "jpeg", ".bmp", "tiff", ".tif"]
save_format = ".png"

gotten = 0

def get_time():
	return time.strftime("%X     ", time.localtime())

def log(text):
	if not silent:
		try:
			print get_time() + str(text)
		except UnicodeEncodeError:
			print get_time() + "(Message cannot display)"

def file_location(test, group, full_file):
	base = subreddits[group][0] + "/" + ["train", "test"][test]
	if full_file == "":
		return base
	return base + "/" + full_file[:-4] + save_format

# Thank you (NOT! These suck) for the following two functions:
# https://github.com/Rookev/Reddit-Image-Scraper

def process_album(url):
	"""
	Processes an imgur album by extracting direct links and downloading them seperately.
	:param url: "http://imgur.com/a/XYZ123"
	"""
	return []

	# Read html file to url
	try:
		htmlpage = requests.get(url).content
	except Exception, e:
		log("Error while opening:\t" + url)
		log(str(e))
		return
	try:
		soup = BeautifulSoup(htmlpage)
	except Exception, e:
		log("Error while parsing:\t" + url)
		log(str(e))
		return

	# Extract image links from html
	urls = soup.select('.album-view-image-link a')
	processed = []
	for url in urls:
		url = url['href']

		# Download image
		url = format_url(url)
		processed.append(url)

	return processed

def format_url(url):
	"""
	Formats url strings by front adding "http:" if needed and removing ?s
	:param url: "//imgur.com/XYZ123?1"
	:return: "http://imgur.com/XYZ123"
	"""
	if url.startswith("//"):
		url = "http:" + url

	# If applicable, remove "?1" at the end of the url
	if "?" in url:
		url = url[:url.find("?")]

	return url

r = praw.Reddit(user_agent="Download training data for /u/me_irl-bot",
	client_id="F31LfxUD3fDzug", client_secret="irgSKcnU5u3skdq940yiXdD4gfo",
	username="me_irl-bot", password="ek5H6CBmXw")

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
		if "-d" in arg: #--day (default)
			scan.append("day")
		if "-f" in arg: # --force
			log("Re-downloading all pictures.")
			force = True
		if "-r" in arg: # --retrain
			log("Re-training from new data after downloading.")
			retrain = True

if len(scan) == 0:
	# Default scan top of day
	scan.append("day")

for scan_type in scan:

	for subreddit_group in range(len(subreddits)):

		matches = subreddit_group != 0

		for subreddit_name in subreddits[subreddit_group]:

			subreddit = r.subreddit(subreddit_name)

			log("Retrieving from /r/" + subreddit_name + "...")

			sub_gotten = 0

			already_count = 0
			failed = False

			submissions_groups = []
			if scan_type == "top":
				submissions_groups = [subreddit.top(limit=1000), subreddit.top("year", limit=1000),
					subreddit.top("month", limit=1000), subreddit.top("week", limit=1000)]
				log("Scanning all top posts.")
			elif scan_type == "hot":
				submissions_groups = [subreddit.hot(limit=1000)]
				log("Scanning all hot posts.")
			else:
				if scan_type != "day":
					log("ERROR: Invalid scan type. Proceeding with --day.")
				submissions_groups = [subreddit.top("day", limit=1000)]
				log("Scanning top posts of today.")

			for submissions in submissions_groups:
				for sub in submissions:

					if (not sub.subreddit in [j for i in subreddits[1:] for j in i]
						and not sub.subreddit in exclude) or matches:

						if already_count > already_threshold and not force:
							failed = True
							log("Already retrieved posts from subreddit.")
							break

						urls = []

						url = format_url(sub.url)
						if "imgur.com/a/" in sub.url or "imgur.com/gallery/" in sub.url:
							urls = process_album(sub.url)
						elif url[-4:] in exts or "i.reddit" in exts:
							urls.append(url)
						elif "imgur.com/" in sub.url and not "." in sub.url[-5:]:
							urls.append(sub.url + ".jpg") # Force direct link

						if urls:
							for url in urls:

								file = url.split("/")[-1]

								if matches:
									# If we have collected this positive as a negative, remove it
									if os.path.exists(file_location(False, 0, file)):
										os.remove(file_location(False, 0, file))
										log("Removing post that was X-posted to a positive sub from the negatives")
									if os.path.exists(file_location(True, 0, file)):
										os.remove(file_location(True, 0, file))
										log("Removing post that was X-posted to a positive sub from the negatives")

								if (not os.path.exists(file_location(False, subreddit_group, file))
									and not os.path.exists(file_location(True, subreddit_group, file))):

									raw = False
									try:
										link = requests.get(url)
										raw = link.content
									except:
										log("Unable to access an image.")
										continue

									image = False
									try:
										image = Image.open(StringIO(raw))
									except:
										log("Unable to process an image.")
										continue

									if image:

										if image.size >= min_size:

											if (not matches and len(subreddits[0]) < top_subreddits
												and not str(sub.subreddit) in subreddits[0]):
												log("Adding subreddit found on /r/all: " + str(sub.subreddit))
												subreddits[0].append(str(sub.subreddit))

											test = random.randint(0, 1)

											if not os.path.exists(file_location(test, subreddit_group, "")):
												group_name = subreddits[subreddit_group][0]
												if not os.path.exists(group_name):
													os.mkdir(group_name)
												os.mkdir(file_location(test, subreddit_group, ""))

											already_count = 0
											gotten += 1
											sub_gotten += 1

											log(sub.title[:100])

											image.thumbnail(max_size, Image.ANTIALIAS * resample)

											try:
												image.save(file_location(test, subreddit_group, file))
											except Exception, e:
												log("Could not save image due to filesystem.")
												log(str(e))

								else:
									already_count += 1

			if not failed:
				log("Retrieved " + str(sub_gotten) + " posts from /r/" + subreddit_name + ".")
			log("------------------------------------------")

log("Retrieved " + str(gotten) + " posts total.")

os.system("python check_sanity.py" + " -auto" * silent)

if retrain:
	log("Retraining with new dataset.")
	for group in subreddits:
		log("Retraining on " + group[0])
		os.system("python learn.py " + group[0])

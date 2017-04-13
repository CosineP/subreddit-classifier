# Train a model to differentiate between subreddits based on OCR processed by mine_ocr.py
import os
import argparse

parser = argparse.ArgumentParser(description="Train a model to differentiate between subreddits based on OCR processed by mine_ocr.py")
parser.add_argument("positive", metavar="pos", help="The subreddit to classify as >0.5.")
parser.add_argument("negative", nargs="?", metavar="neg", default="all", help="The subreddit to classify as <0.5 (default all).")
parser.add_argument("--epochs", "-e", type=int, default=4, help="Number of times to iterate through the entire training set.")
parser.add_argument("--max-length", "-m", dest="max_length", type=int, default=100, help="The maximum length of OCR caption to read. Will be truncated and padded.")
# parser.add_argument("--early-stopping", dest="stop", action="store_true", help="Whether or not to stop training when test loss stops decreasing.")
parser.add_argument("--batch-size", "-b", dest="batch_size", type=int, default=32, help="Number of images to train on at a time (more memory but better training).")
parser.add_argument("--load-batch-size", "-l", dest="load_batch_size", type=int, default=8192, help="Number of bytes of OCR to read at a time (not neccessarily to train on).")
# parser.add_argument("--visualize", "-v", action="store_true", help="Post results to server running hualos on localhost:9000.")
# parser.add_argument("--treat-categorical", "-c", dest="treat_categorical", action="store_true", help="Train as a categorical classification with two classes instead of binary.")
# parser.add_argument("--weight", "-w", action="store", default=None, help="Automatically determine appropriate weights for unbalanced class sizes.")
# parser.add_argument("--no-save", "-n", dest="save", action="store_false", help="Do not save model (use for testing only!).")
args = parser.parse_args()

# Some imports auto-initialize, so imports need to occur after argument reading so as to avoid waiting, only to find out you made a typo
import numpy as np
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from keras.layers.embeddings import Embedding
from keras.preprocessing import sequence


np.random.seed(147) # Same as CNN
#x_train = sequence.pad_sequences(dd
char_max = 0x7e
char_min = 0x0a
num_letters = char_max - char_min + 1
embedding_vector_length = 32
delim = "@!@"

model = Sequential()
model.add(Embedding(num_letters, embedding_vector_length, input_length=args.max_length))
model.add(LSTM(100))
model.add(Dense(1, activation='sigmoid'))
model.compile(loss="binary_crossentropy", optimizer="adam", metrics=["precision"])
print model.summary()

def convert(string):
	return [ord(c) - char_min for c in string] 

def count_delims(filename):
	source = open(filename)
	count = 0
	while True:
		chunk = source.read(args.load_batch_size)
		if not chunk:
			break
		count += chunk.count(delim)
	source.close()
	return count

def read_entry(source):
	buf = ""
	while True:
		while delim in buf:
			pos = buf.index(delim)
			yield (convert(buf[:pos]), False)
			buf = buf[pos + len(delim):]
		chunk = source.read(args.load_batch_size)
		if not chunk:
			yield (convert(buf), True)
			break
		buf += chunk

def generator(isTest):
	while True:
		for is_positive in range(2):
			class_name = [args.negative, args.positive][is_positive]
			source = open("ocr/" + ["train", "test"][isTest] + "/" + class_name + ".txt")
			done = False
			while not done:
				batch = []
				for i in range(args.batch_size):
					entry, done = read_entry(source).next()
					batch.append(entry)
					if done:
						break
				yield sequence.pad_sequences(batch, maxlen=args.max_length), [is_positive]*len(batch)
			source.close()

def train_generator():
	return generator(False)

def test_generator():
	return generator(True)

# TODO: MAKE WORK
nb_train_samples = count_delims("ocr/train/" + args.negative + ".txt") + count_delims("ocr/train/" + args.positive + ".txt") + 2
print "Training on:"
print nb_train_samples
model.fit_generator(train_generator(), nb_train_samples, nb_epoch=args.epochs, validation_data=test_generator(), nb_val_samples=nb_test_samples)


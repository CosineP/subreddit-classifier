import os
import argparse
from time import sleep

# For testing only
from matplotlib import pyplot

import numpy
from keras.models import Sequential
from keras.layers import Convolution2D, MaxPooling2D, Activation, Dense, Flatten, Dropout
from keras.preprocessing.image import ImageDataGenerator
from keras.callbacks import RemoteMonitor, EarlyStopping
from keras import backend
# from sklearn.metrics import confusion_matrix # One day. ONE DAY.


parser = argparse.ArgumentParser(description="Train and save a model based on the training data.")
parser.add_argument("positive", metavar="pos", help="The subreddit to classify as >0.5.")
parser.add_argument("negative", nargs="?", metavar="neg", default="all", help="The subreddit to classify as <0.5 (default all).")
parser.add_argument("--epochs", "-e", type=int, default=64, help="Number of times to iterate through the entire training set.")
parser.add_argument("--early-stopping", dest="stop", action="store_true", help="Whether or not to stop training when test loss stops decreasing.")
parser.add_argument("--batch-size", "-b", dest="batch_size", type=int, default=32, help="Number of images to train on at a time (more memory but better training).")
parser.add_argument("--visualize", "-v", action="store_true", help="Post results to server running hualos on localhost:9000.")
parser.add_argument("--treat-categorical", "-c", dest="treat_categorical", action="store_true", help="Train as a categorical classification with two classes instead of binary.")
parser.add_argument("--size", "-s", nargs=2, type=int, default=(200, 200), help="Size to resize images to in memory before training.")
parser.add_argument("--weight", "-w", action="store", default=None, help="Automatically determine appropriate weights for unbalanced class sizes.")
parser.add_argument("--no-save", "-n", dest="save", action="store_false", help="Do not save model (use for testing only!).")
args = parser.parse_args()

print "Learning to classify subreddit " + args.positive

numpy.random.seed(147) # Deterministic. Number arbitrary
backend.set_image_dim_ordering("th")

model = Sequential()
model.add(Convolution2D(32, 3, 3, input_shape=(3, 200, 200)))
model.add(Activation('relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))

model.add(Convolution2D(32, 3, 3))
model.add(Activation('relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))

model.add(Convolution2D(64, 3, 3))
model.add(Activation('relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))

model.add(Flatten())  # this converts our 3D feature maps to 1D feature vectors
model.add(Dense(64))
model.add(Activation('relu'))
model.add(Dropout(0.5))
model.add(Dense([1, 2][args.treat_categorical]))
model.add(Activation(['sigmoid', 'softmax'][args.treat_categorical]))

# TODO: Try balancing data
metrics = ["precision", "matthews_correlation"]
model.compile(loss=['binary_crossentropy', 'categorical_crossentropy'][args.treat_categorical], optimizer='rmsprop', metrics=metrics)

# train_generator = 0
# if args.positive == "me_irl":
train_generator = ImageDataGenerator(rescale=1./255, shear_range=0.2, zoom_range=0.2)
# elif args.positive == "test":
#     train_generator = ImageDataGenerator(rescale=1./255)
# else:
#     train_generator = ImageDataGenerator(rescale=1./255, width_shift_range=0.2, height_shift_range=0.2, zoom_range=0.2,
#         shear_range=0.2, rotation_range=0.2, channel_shift_range=0.2, horizontal_flip=True)
train_generator = train_generator.flow_from_directory("", classes=[args.negative + "\\train", args.positive + "\\train"],
	target_size=args.size, batch_size=args.batch_size, class_mode=["binary", "categorical"][args.treat_categorical])
test_generator = ImageDataGenerator(rescale=1./255).flow_from_directory("", classes=[args.negative + "\\test", args.positive + "\\test"],
	target_size=args.size, batch_size=args.batch_size, class_mode=["binary", "categorical"][args.treat_categorical])

# get_3rd_layer_output = backend.function([model.layers[0].input], [model.layers[3].output])
# layer_output = get_3rd_layer_output([test_generator.next()[0]])[0]
# print layer_output[0][0:3].transpose().shape
# image = Image.fromarray(layer_output[0][0:3].transpose())
# image.save("test.png")

callbacks = [EarlyStopping(monitor="val_loss", min_delta=0.001, patience=5, mode="auto")]
if args.visualize:
	callbacks.append(RemoteMonitor(root="http://localhost:9000"))

try:
	model.fit_generator(train_generator, train_generator.nb_sample, args.epochs,
		validation_data=test_generator, nb_val_samples = train_generator.nb_sample/5,
		callbacks=callbacks, class_weight=args.weight)
	print "\x07"
except Exception, e:
	print "Error during training:"
	print str(e)
	for i in range(3):
		print "\x07"
		sleep(1)
	if "n" in raw_input("Would you still like to save the weights? (Y/n) "):
		exit()

print "Example predictions:"
print model.predict([test_generator.next()[0]])
print "Evaluating on entire test set..."
accuracy = int(model.evaluate_generator(test_generator, test_generator.nb_sample)[1] * 100)

if args.save:
	folder = "models\\"
	name = folder + args.positive + ("-" + args.negative) * (args.negative != "all") + "-" + metrics[0] + "=" + str(accuracy)
	default_name = folder + args.positive + ("-" + args.negative) * (args.negative != "all")
	weight_ext = ".h5"
	json_ext = ".json"
	print "Saving weights in " + name
	if os.path.exists(default_name + weight_ext):
		os.remove(default_name + weight_ext)
	if os.path.exists(default_name + json_ext):
		os.remove(default_name + json_ext)
	i = 2
	num_ext = ""
	while os.path.exists(name + num_ext + weight_ext):
		num_ext = "-#" + str(i)
		i += 1
	if i != 2:
		name = name + num_ext
		print "Model with equal ability already found."
		print "Naming " + name
	json_file = open(name + json_ext, "w")
	json_file.write(model.to_json())
	json_file.close()
	json_file = open(default_name + json_ext, "w")
	json_file.write(model.to_json())
	json_file.close()
	model.save_weights(name + weight_ext)
	model.save_weights(default_name + weight_ext)

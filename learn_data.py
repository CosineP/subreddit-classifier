import numpy
from keras.models import Sequential
from keras.layers import Convolution2D, MaxPooling2D, Activation, Dense, Flatten, Dropout
from keras.preprocessing.image import ImageDataGenerator
from keras.callbacks import RemoteMonitor, EarlyStopping
from keras import backend
# from sklearn.metrics import confusion_matrix

 # For testing only
from matplotlib import pyplot
from PIL import Image

from sys import argv
import os
from time import sleep

# Defaults. Command-line options specify
project = ""
negative_sub = "all"
categorical_binary = False
epochs = 64
class_weight = None
batch_size = 64
test = False
size = (200, 200)
visualize = False

argc = len(argv)
if argc > 1:
	project = argv[1]
	if argc > 2:
		if "-" in argv[2]:
			for i in range(2, argc):
				if "-e" in argv[i]: # epochs
					if argc > i + 1:
						epochs = int(argv[i + 1])
						print "Training " + str(epochs) + " epochs."
					else:
						print "Please specify epoch size with -e flag."
				if "-s" in argv[i]: # size
					if argc > i + 2:
						size = (int(argv[i+1]), int(argv[i+2]))
						print "Sizing images to " + str(size) + "."
					else:
						print "Please specify two dimensions with -s flag. Eg -s 200 200"
				if "-b" in argv[i]:
					if argc > i + 1:
						batch_size = int(argv[i + 1])
						print "Using batches of size " + batch_size + "."
					else:
						print "Please specify batch size with -b flag."
				if "-v" in argv[i]:
					visualize = True
					print "Visualizing data with hualos. Make sure api.py is running!"
				if "-c" in argv[i]:
					categorical_binary = True
					print "Using two categorical classes to represent binary classification."
				if "-w" in argv[i]:
					class_weight = "auto"
					print "Automatically weighting for fair treatment of classes."
				if "-t" in argv[i]:
					test = True
					print "Not saving weights, running a test."
		else:
			negative_sub = argv[2]
else:
	print 'Error: Fatal: Please specify a project name (subreddit name eg "me_irl").'
	exit()

print "Learning to classify subreddit " + project

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
model.add(Dense([1, 2][categorical_binary]))
model.add(Activation(['sigmoid', 'softmax'][categorical_binary]))

# TODO: Try balancing data
metrics = ["precision", "matthews_correlation"]
model.compile(loss=['binary_crossentropy', 'categorical_crossentropy'][categorical_binary], optimizer='rmsprop', metrics=metrics)

# train_generator = 0
# if project == "me_irl":
train_generator = ImageDataGenerator(rescale=1./255, shear_range=0.2, zoom_range=0.2)
# elif project == "test":
#     train_generator = ImageDataGenerator(rescale=1./255)
# else:
#     train_generator = ImageDataGenerator(rescale=1./255, width_shift_range=0.2, height_shift_range=0.2, zoom_range=0.2,
#         shear_range=0.2, rotation_range=0.2, channel_shift_range=0.2, horizontal_flip=True)
train_generator = train_generator.flow_from_directory("", classes=[negative_sub + "\\train", project + "\\train"],
	target_size=size, batch_size=batch_size, class_mode=["binary", "categorical"][categorical_binary])
test_generator = ImageDataGenerator(rescale=1./255).flow_from_directory("", classes=[negative_sub + "\\test", project + "\\test"],
	target_size=size, batch_size=batch_size, class_mode=["binary", "categorical"][categorical_binary])

# get_3rd_layer_output = backend.function([model.layers[0].input], [model.layers[3].output])
# layer_output = get_3rd_layer_output([test_generator.next()[0]])[0]
# print layer_output[0][0:3].transpose().shape
# image = Image.fromarray(layer_output[0][0:3].transpose())
# image.save("test.png")

callbacks = [EarlyStopping(monitor="val_loss", min_delta=0.001, patience=5, verbose=1, mode="auto")]
if visualize:
	callbacks.append(RemoteMonitor(root="http://localhost:9000"))

try:
	model.fit_generator(train_generator, train_generator.nb_sample, epochs,
		validation_data=test_generator, nb_val_samples = train_generator.nb_sample/5,
		callbacks=callbacks, class_weight=class_weight)
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

if not test:
	folder = "models\\"
	name = folder + project + ("-" + negative_sub) * (negative_sub != "all") + "-" + metrics[0] + "=" + str(accuracy)
	default_name = folder + project + ("-" + negative_sub) * (negative_sub != "all")
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
		print "Model with equal ability already found."
		print "Naming " + name
		name = name + num_ext
	json_file = open(name + json_ext, "w")
	json_file.write(model.to_json())
	json_file.close()
	json_file = open(default_name + json_ext, "w")
	json_file.write(model.to_json())
	json_file.close()
	model.save_weights(name + weight_ext)
	model.save_weights(default_name + weight_ext)
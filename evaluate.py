import numpy
from keras.models import model_from_json
from keras.preprocessing.image import ImageDataGenerator
from keras import backend
from theano import tensor as T

 # For testing only
from matplotlib import pyplot
from PIL import Image

from sys import argv
import os

# from sklearn.metrics import confusion_matrix
from keras.metrics import precision
# Defaults. Command-line options specify
project = ""
negative_sub = "all"
name = ""
categorical_binary = False
size = (200, 200)
batch_size = 32

argc = len(argv)
if argc > 1:
	project = argv[1]
	if argc > 2:
		negative_sub = argv[2]
		if argc > 3:
			name = argv[3]
			if argc > 4:
				for i in range(4, argc):
					if "-s" in argv[i]: # size
						if argc > i + 2:
							size = (int(argv[i+1]), int(argv[i+2]))
							print "Sizing images to " + str(size) + "."
						else:
							print "Please specify two dimensions with -s flag. Eg -s 200 200"
					if "-c" in argv[i]: # size
						categorical_binary = True
						print "Using two categorical classes to represent binary classification"
					if "-b" in argv[i]:
						if argc > i + 1:
							batch_size = int(argv[i + 1])
							print "Using batches of size " + batch_size + "."
						else:
							print "Please specify batch size with -b flag."
		else:
			name = project + ("-" + negative_sub) * (negative_sub != "all")
	else:
		name = project
else:
	print 'Error: Fatal: Please specify a project file name ("me_irl" or "me_irl-matthews_correlation=22").'
	exit()

numpy.random.seed(147) # Deterministic. Number arbitrary
numpy.set_printoptions(precision=4, suppress=True, threshold=200)
backend.set_image_dim_ordering("th")

print "Loading model..."

name = "models/" + name

model = ""
file = open(name + ".json")
model = model_from_json(file.read())
file.close()
model.load_weights(name + ".h5")

# y_true = T.matrix("y_true")
# print precision([[.2, .8], [.7, .3]], [[1, 0], [0, 1]])


# def confusion_matrix(y_true,y_pred):
#     return T.eq(y_true, y_pred)
#
# # def confusion_matrix_keras_callback(y_true, y_pred):
# # 	# print y_true.ndim
# # 	return confusion_matrix(y_true, y_pred)

loss_function = ['binary_crossentropy', 'categorical_crossentropy'][categorical_binary]
metrics_names = [loss_function, "precision", "recall", ["matthews_correlation", "categorical_accuracy"][categorical_binary]]
model.compile(loss=loss_function, optimizer='rmsprop', metrics=metrics_names[1:])

test_generator = ImageDataGenerator(rescale=1./255).flow_from_directory("", classes=[negative_sub + "/test", project + "/test"],
target_size=size, batch_size=batch_size, class_mode=["binary", "categorical"][categorical_binary])

print "Evaluating on entire test set..."
metrics = model.evaluate_generator(test_generator, test_generator.nb_sample)

batch = test_generator.next()
print "Sample predictions:"
if categorical_binary:
	# TODO: Figure out how to zip these
	print model.predict(batch[0])
	print batch[1]
else:
	print numpy.vstack([model.predict([batch[0]]).T, batch[1]]).T
print "Full metrics:"
print metrics
print "Breakdown:"
for i in range(len(metrics_names)):
	print "Final " + metrics_names[i] + ": " + str(int(metrics[i] * 100 + 0.5))

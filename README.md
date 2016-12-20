Subreddit Classifier
===

This is a toolkit for classifying *images* from different subreddits from reddit.com. It downloads as many pictures from /r/all and a few chosen subreddits and sorts them for training / test data. It then (as of now) uses a Convolutional Neural Network to train on training data and learn to classify images by sub.

In the future it will be used to do funny things with false-positives. For example, the original hope was to classify images in /r/all that would "belong" in /r/me_irl and post "Me too thanks."

As of now this repository contains:

 - Python scripts for downloading and maintaining data
 - Python scripts for learning the data using a CNN
 - A few preliminary python scripts for using the trained networks
 - Saved models in .json form, without their weights (only local)

Not included in the repository are:

 - All of the training data, sorted by subreddit and split into test/train
 - Model weights with the same name as the .json files except .h5

# -*- coding: utf-8 -*-
"""project03_CNN.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1c6n-0-AnfV8jyyI7MsB2RX1cEKGCT_59

# Imports
"""

# Commented out IPython magic to ensure Python compatibility.
# %%shell
# jupyter nbconvert --to html "/content/project03_CNN.ipynb"

import tensorflow as tf
tf.test.gpu_device_name()
import nltk
nltk.download("stopwords")
nltk.download('punkt')

import pandas as pd
import numpy as np
import random
import re
import matplotlib.pyplot as plt

from nltk import word_tokenize, sent_tokenize
from gensim.models import Word2Vec, KeyedVectors

from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.metrics import confusion_matrix, accuracy_score, classification_report
from sklearn.model_selection import train_test_split

from keras import Sequential, Model
from keras import layers
from keras.utils import to_categorical
from keras.callbacks import EarlyStopping
from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences
from keras.utils.vis_utils import plot_model
from nltk.corpus import stopwords as STOPWORDS

stopWords = set(STOPWORDS.words('turkish'))

"""# Preparing Data"""

folder_path = "/content/drive/MyDrive/CS 445 Project 3"

def plotHistory(history):
    # Plot training & validation accuracy values
    plt.plot(history.history['accuracy'])
    plt.plot(history.history['val_accuracy'])
    plt.title('Model accuracy')
    plt.ylabel('Accuracy')
    plt.xlabel('Epoch')
    plt.legend(['Train', 'Validation'], loc='upper left')
    plt.show()

    # Plot training & validation loss values
    plt.plot(history.history['loss'])
    plt.plot(history.history['val_loss'])
    plt.title('Model loss')
    plt.ylabel('Loss')
    plt.xlabel('Epoch')
    plt.legend(['Train', 'Validation'], loc='upper left')
    plt.show()

def preprocess(docs):
    result = []
    for d in docs:
        a = re.sub(r'[\'’\"”][\w]+ ', " " ,d)
        for stopword in stopWords:
            a = a.replace(" "+ stopword + " ", " ")
        a = re.sub(r'[“’‘\'\"”…]', "", a)
        a = re.sub(r'\d+', "", a)
        a = a.replace("  ", " ")
        result.append(a.lower())
    return result

def read_data(path):
    data = pd.read_csv(path)
    return data

path = folder_path + "/dataset/train.csv"
data = read_data(path)

path = folder_path +  "/dataset/test.csv"
test_data = read_data(path)

data_text = data["text"]
data_label = data["label"]

test_data_text = test_data["text"]
test_data_label = test_data["label"]

class_mapping = {
    "turkiye": 0,
    "dunya": 1,
    "spor": 2,
    "video": 3,
    "yazarlar": 4,
}

data_text[0]

data_text = preprocess(data_text)
test_data_text = preprocess(test_data_text)

data_text[0]

"""# Choose Pre-Trained Embedding"""

EMBEDDING_DIM = 400

word_vectors = KeyedVectors.load_word2vec_format(folder_path + '/trmodel', binary=True)

EMBEDDING_DIM = 300

word_vectors = KeyedVectors.load_word2vec_format(folder_path + "/CBOW_100k_300_10.txt", binary=False)

EMBEDDING_DIM = 200

word_vectors = KeyedVectors.load_word2vec_format(folder_path + "/CBOW_100k_200_10.txt", binary=False)

EMBEDDING_DIM = 100

word_vectors = KeyedVectors.load_word2vec_format(folder_path + "/CBOW_100k_100_10.txt", binary=False)

EMBEDDING_DIM = 300

word_vectors = KeyedVectors.load_word2vec_format(folder_path + "/Skipgram_100k_300_10.txt", binary=False)

EMBEDDING_DIM = 200

word_vectors = KeyedVectors.load_word2vec_format(folder_path + "/Skipgram_100k_200_10.txt", binary=False)

EMBEDDING_DIM = 100

word_vectors = KeyedVectors.load_word2vec_format(folder_path + "/Skipgram_100k_100_10.txt", binary=False)

"""# CNN"""

from datetime import date, datetime

accuracyLogsFile = open(folder_path + "/CNN_Accuracies.txt", "w")

def runAll(data_text, data_label, test_data_text, test_data_label, pre_trained_embedding , train_embedding, patience, EMBEDDING_DIM, word_vectors, name):
    tokenizer = Tokenizer()
    tokenizer.fit_on_texts(data_text)
    
    encoded_docs = tokenizer.texts_to_sequences(data_text)

    max_length = max([len(s.split()) for s in data_text])
    Xtrain = pad_sequences(encoded_docs, maxlen=max_length, padding='post')

    vocab_size = len(tokenizer.word_index) + 1

    word_index = tokenizer.word_index

    if pre_trained_embedding:
        count = 0
        embedding_matrix = np.zeros((vocab_size, EMBEDDING_DIM))
        
        for word, i in word_index.items():
            try:
                embedding_vector = word_vectors[word]
                embedding_matrix[i] = embedding_vector
            except KeyError:
                count += 1
                # if random.randint(0,19) == 0:
                #     print(word,"removed")
                embedding_matrix[i]=np.random.normal(0,np.sqrt(0.25),EMBEDDING_DIM)

        print("************\n", count, "many word randomized.\n************\n")

        # del(word_vectors)

    train_labels = np.array( data_label.map(class_mapping) )
    # train_labels = to_categorical(train_labels, 5)

    y_test = np.array( test_data_label.map(class_mapping) )
    # y_test = to_categorical(y_test, 5)

    X_train, X_valid, y_train, y_valid = train_test_split(
                                                    Xtrain,
                                                    train_labels,
                                                    test_size = 0.1,
                                                    random_state = 42)

    encoded_docs = tokenizer.texts_to_sequences(test_data_text)

    X_test = pad_sequences(encoded_docs, maxlen=max_length, padding='post')

    if pre_trained_embedding:
        print("Pre-Trained Word Embedding")
        embedding_layer = layers.Embedding(vocab_size,
                                EMBEDDING_DIM,
                                input_length=max_length,
                                weights=[embedding_matrix],
                                trainable=train_embedding,
                                input_shape=(X_train.shape[1],)
                                )
    else:
        print("Randomized Word Embedding")
        embedding_layer = layers.Embedding(vocab_size,
                                    EMBEDDING_DIM,
                                    input_length=max_length,
                                    trainable=train_embedding,
                                    input_shape=(X_train.shape[1],)
                                ) 

    model = Sequential()

    model.add(embedding_layer)

    model.add(layers.Conv1D(filters=128, kernel_size=8, padding="same", activation='relu'))

    model.add(layers.Dropout(rate=0.5))

    model.add(layers.MaxPooling1D(pool_size=2))

    model.add(layers.Flatten())

    model.add(layers.Dense(10, activation='relu'))

    model.add(layers.Dense(5, activation='softmax'))

    es_loss = EarlyStopping(monitor='val_loss', patience=4)
    es_acc = EarlyStopping(monitor='val_accuracy', patience=4)

    model.compile(loss='sparse_categorical_crossentropy',
              optimizer = "adam",
              metrics=['accuracy'])

    print(model.summary())

    plot_model(model, show_shapes=True , to_file=folder_path + "/Model Layers/Model Layers_" + name + ".png")

    model.save(folder_path + "/Saved Model Weights/Model_Weights_" + name + ".h5")

    history = model.fit(    X_train , y_train,
                            epochs=20,
                            validation_data=(X_valid, y_valid),
                            callbacks=[es_loss, es_acc], 
                            verbose=1)
    
    plotHistory(history)

    loss, accuracy = model.evaluate( X_test, y_test, verbose=False )
    print("Test Loss:", loss, "\nTest Accuray:", accuracy)

    now = datetime.now()

    accuracyLogsFile.write("Time: " + str(now.strftime("%Y-%m-%d %H:%M:%S")) + "\n")
    accuracyLogsFile.write("\tModel Type: "  + name + "\tPreTrainedEmbedding: " + str(pre_trained_embedding) + "\tTrainEmbedding: " + str(train_embedding) + "\n")
    accuracyLogsFile.write( "\t\tTest Loss: " + str(loss)  + "\n\t\tTest Accuray: " + str(accuracy) + "\n\n\n" )

_pre_trained_embedding = True
_train_embedding = True
# EMBEDDING_DIM = 400
# word_vectors = []

runAll( data_text, data_label, test_data_text, test_data_label,
            pre_trained_embedding = _pre_trained_embedding,
            train_embedding = _train_embedding,
            patience = 4,
            EMBEDDING_DIM = EMBEDDING_DIM,
            word_vectors = word_vectors,
            name = "Skipgram_200D", )

accuracyLogsFile.close()

"""# CNN Codes Separately"""

tokenizer = Tokenizer()

tokenizer.fit_on_texts(data_text)

encoded_docs = tokenizer.texts_to_sequences(data_text)

max_length = max([len(s.split()) for s in data_text])
Xtrain = pad_sequences(encoded_docs, maxlen=max_length, padding='post')

vocab_size = len(tokenizer.word_index) + 1

word_index = tokenizer.word_index

count = 0

embedding_matrix = np.zeros((vocab_size, EMBEDDING_DIM))
for word, i in word_index.items():
    try:
        embedding_vector = word_vectors[word]
        embedding_matrix[i] = embedding_vector
    except KeyError:
        count += 1
        # if random.randint(0,19) == 0:
        #     print(word,"removed")
        embedding_matrix[i]=np.random.normal(0,np.sqrt(0.25),EMBEDDING_DIM)

print(count, "many word removed.", word)

del(word_vectors)

train_labels = np.array( data_label.map(class_mapping) )
train_labels = to_categorical(train_labels, 5)

y_test = np.array( test_data_label.map(class_mapping) )
y_test = to_categorical(y_test, 5)

X_train, X_valid, y_train, y_valid = train_test_split(
                                                    Xtrain,
                                                    train_labels,
                                                    test_size= 0.1,
                                                    random_state=1)

encoded_docs = tokenizer.texts_to_sequences(test_data_text)

X_test = pad_sequences(encoded_docs, maxlen=max_length, padding='post')


data_text = []
data_label = []
test_data_text = []
test_data_label = []

embedding_layer = layers.Embedding(vocab_size,
                            EMBEDDING_DIM,
                            input_length=max_length,
                            weights=[embedding_matrix],
                            trainable=True,
                            input_shape=(X_train.shape[1],)
                            )

EMBEDDING_DIM = 100

embedding_layer = layers.Embedding(vocab_size,
                            EMBEDDING_DIM,
                            input_length=max_length,
                            trainable=False,
                            input_shape=(X_train.shape[1],) )

model = Sequential()

model.add(embedding_layer)

# model.add()

# model.add(layers.Conv1D(filters=128, kernel_size=2, padding="same", activation='relu'))

# model.add(layers.MaxPooling1D(pool_size=2))

# model.add(layers.Conv1D(filters=128, kernel_size=3, padding="same", activation='relu'))

# model.add(layers.MaxPooling1D(pool_size=3))

model.add(layers.Conv1D(filters=128, kernel_size=8, padding="same", activation='relu'))

model.add(layers.MaxPooling1D(pool_size=4))

model.add(layers.Flatten())

model.add(layers.Dense(128, activation='relu'))

model.add(layers.Dropout(rate=0.5))

model.add(layers.Dense(5, activation='softmax'))

"""# MultiChannel CNN"""

tokenizer = Tokenizer()
tokenizer.fit_on_texts(data_text)

encoded_docs = tokenizer.texts_to_sequences(data_text)

max_length = max([len(s.split()) for s in data_text])
Xtrain = pad_sequences(encoded_docs, maxlen=max_length, padding='post')

vocab_size = len(tokenizer.word_index) + 1

word_index = tokenizer.word_index

count = 0
embedding_matrix = np.zeros((vocab_size, EMBEDDING_DIM))

for word, i in word_index.items():
    try:
        embedding_vector = word_vectors[word]
        embedding_matrix[i] = embedding_vector
    except KeyError:
        count += 1
        # if random.randint(0,19) == 0:
        #     print(word,"removed")
        embedding_matrix[i]=np.random.normal(0,np.sqrt(0.25),EMBEDDING_DIM)

print("************\n", count, "many word randomized.\n************\n")

# del(word_vectors)

train_labels = np.array( data_label.map(class_mapping) )
train_labels = to_categorical(train_labels, 5)

y_test = np.array( test_data_label.map(class_mapping) )
y_test = to_categorical(y_test, 5)

X_train, X_valid, y_train, y_valid = train_test_split(
                                                Xtrain,
                                                train_labels,
                                                test_size = 0.1,
                                                random_state = 42)

encoded_docs = tokenizer.texts_to_sequences(test_data_text)

X_test = pad_sequences(encoded_docs, maxlen=max_length, padding='post')

length = X_train.shape[1]

from keras.models import Model
from keras.layers import Input
from keras.layers import Dense
from keras.layers import Flatten
from keras.layers import Dropout
from keras.layers import Embedding
from keras.layers.convolutional import Conv1D
from keras.layers.convolutional import MaxPooling1D
from keras.layers.merge import concatenate

# channel 1
inputs1 = Input(shape=(length,))
embedding1 = Embedding(vocab_size,
                                EMBEDDING_DIM,
                                input_length=max_length,
                                weights=[embedding_matrix],
                                trainable=True,
                                input_shape=(X_train.shape[1],)
                                )(inputs1)
conv1 = Conv1D(filters=32, kernel_size=3, activation='relu')(embedding1)
drop1 = Dropout(0.5)(conv1)
pool1 = MaxPooling1D(pool_size=2)(drop1)
flat1 = Flatten()(pool1)
# channel 2
inputs2 = Input(shape=(length,))
embedding2 = Embedding(vocab_size,
                                EMBEDDING_DIM,
                                input_length=max_length,
                                weights=[embedding_matrix],
                                trainable=True,
                                input_shape=(X_train.shape[1],)
                                )(inputs2)
conv2 = Conv1D(filters=32, kernel_size=5, activation='relu')(embedding2)
drop2 = Dropout(0.5)(conv2)
pool2 = MaxPooling1D(pool_size=2)(drop2)
flat2 = Flatten()(pool2)
# channel 3
inputs3 = Input(shape=(length,))
embedding3 = Embedding(vocab_size,
                                EMBEDDING_DIM,
                                input_length=max_length,
                                weights=[embedding_matrix],
                                trainable=True,
                                input_shape=(X_train.shape[1],)
                                )(inputs3)
conv3 = Conv1D(filters=32, kernel_size=7, activation='relu')(embedding3)
drop3 = Dropout(0.5)(conv3)
pool3 = MaxPooling1D(pool_size=2)(drop3)
flat3 = Flatten()(pool3)
# merge
merged = concatenate([flat1, flat2, flat3])
# interpretation
dense1 = Dense(10, activation='relu')(merged)
outputs = Dense(5, activation='softmax')(dense1)
model = Model(inputs=[inputs1, inputs2, inputs3], outputs=outputs)

es_loss = EarlyStopping(monitor='val_loss', patience=4)
es_acc = EarlyStopping(monitor='val_accuracy', patience=4)

model.compile(loss='categorical_crossentropy',
              optimizer = "adam",
              metrics=['accuracy'])

model.summary()

plot_model(model, show_shapes=True , to_file="/content/drive/MyDrive/CS 445 Project 3/Multichannel Model Layers.png")

# history = model.fit(    X_train , y_train,
#                         epochs=20,
#                         # validation_data=(X_valid, y_valid),
#                         # callbacks=[es_loss, es_acc], 
#                         verbose=1)

history = model.fit(  [X_train,X_train,X_train],
            np.array(y_train),
            epochs=10,
            validation_data=( [X_valid, X_valid, X_valid], np.array(y_valid) ),
            callbacks=[es_loss, es_acc],
            batch_size=16, )

print("DONE")

plotHistory(history)

loss, accuracy = model.evaluate([X_test, X_test, X_test] , np.array(y_test), verbose=False )
print("Loss:", loss, "\nAccuray:", accuracy)
# -*- coding: utf-8 -*-
"""UNet_cityscapes.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1urSpoBiIO_550N5UZb5YuDE4RKU4Dbgh
"""

# Commented out IPython magic to ensure Python compatibility.
import tensorflow as tf
import numpy as np
import os
import glob
import matplotlib.pyplot as plt
from keras.models import *
from keras.layers import *
from keras.optimizers import *
from keras.callbacks import ModelCheckpoint, LearningRateScheduler, ReduceLROnPlateau, TensorBoard, EarlyStopping
from keras.models import Model
from keras.layers import Input, BatchNormalization, Conv2D, MaxPooling2D, Dropout, concatenate, merge, UpSampling2D
# %matplotlib inline

train_image_path = "/content/drive/MyDrive/Colab Notebooks/Cityscapes/images/train/*/*.png"
train_label_path = "/content/drive/MyDrive/Colab Notebooks/Cityscapes/gtFine/train/*/*_gtFine_labelIds.png"
val_image_path = "/content/drive/MyDrive/Colab Notebooks/Cityscapes/images/val/*/*.png"
val_label_path = "/content/drive/MyDrive/Colab Notebooks/Cityscapes/gtFine/val/*/*_gtFine_labelIds.png"

train_images = sorted(glob.glob(train_image_path))
train_labels = sorted(glob.glob(train_label_path))
val_images = sorted(glob.glob(val_image_path))
val_labels = sorted(glob.glob(val_label_path))

train_images[1], train_labels[1], val_images[1], val_labels[1]

len(train_images ), len(val_images), len(train_labels), len(val_labels)

dataset_train = tf.data.Dataset.from_tensor_slices((train_images, train_labels))
dataset_val = tf.data.Dataset.from_tensor_slices((val_images, val_labels))

def read_png(path, channels=3): 
    img = tf.io.read_file(path)
    img = tf.image.decode_png(img, channels=channels)
    return img

def crop_img(img, label):
    concat_img = tf.concat([img, label], axis=-1)
    concat_img = tf.image.resize(concat_img, (280, 280), method=tf.image.ResizeMethod.NEAREST_NEIGHBOR)
    crop_img = tf.image.random_crop(concat_img, [256, 256, 4])
    return crop_img[:, :, 0:3], crop_img[:, :, 3:]

def normal(img, label):
    img = tf.cast(img, tf.float32)/127.5 -1
    label = tf.cast(label, tf.int32)
    return img, label

def load_image_train(img_path, label_path):
    img = read_png(img_path)
    label = read_png(label_path, channels=1)
    img, label = crop_img(img, label)
    if tf.random.uniform(()) > 0.5:
        img = tf.image.flip_left_right(img)
        label = tf.image.flip_left_right(label)           
    img, label = normal(img, label)
    return img, label

def load_image_val(img_path, label_path):
    
    img = read_png(img_path)
    label = read_png(label_path, channels=1)
    
    img = tf.image.resize(img, (256, 256))
    label = tf.image.resize(label, (256, 256))
    
    img, label = normal(img, label)
    return img, label

index = np.random.permutation(len(train_images))
train_images = np.array(train_images)[index]
train_labels = np.array(train_labels)[index]

BATCH_SIZE = 32
BUFFER_SIZE = 300
EPOCHS = 50
train_count = len(train_images)
val_count = len(val_images)
train_step_per_epoch = train_count // BATCH_SIZE
val_step_per_epoch = val_count // BATCH_SIZE
auto = tf.data.experimental.AUTOTUNE

dataset_train = dataset_train.map(load_image_train, num_parallel_calls=auto)
dataset_val =dataset_val.map(load_image_val, num_parallel_calls=auto)

for img, label in dataset_train.take(1):
    plt.subplot(1, 2, 1)
    plt.imshow((img + 1)/2)
    plt.subplot(1, 2, 2)
    plt.imshow(np.squeeze(label))

for img, label in dataset_val.take(1):
    plt.subplot(1, 2, 1)
    plt.imshow((img + 1)/2)
    plt.subplot(1, 2, 2)
    plt.imshow(np.squeeze(label))

dataset_train = dataset_train.cache().repeat().shuffle(BUFFER_SIZE).batch(BATCH_SIZE).prefetch(auto)
dataset_val = dataset_val.cache().batch(BATCH_SIZE)

def create_model():
    inputs = tf.keras.layers.Input(shape=(256, 256, 3))
    
    x = tf.keras.layers.Conv2D(64, 3, padding='same', activation='relu')(inputs)
    x = tf.keras.layers.BatchNormalization()(x)    
    x = tf.keras.layers.Conv2D(64, 3, padding='same', activation='relu')(x)
    x = tf.keras.layers.BatchNormalization()(x)

    x1 = tf.keras.layers.MaxPooling2D(padding='same')(x)
    
    x1 = tf.keras.layers.Conv2D(128, 3, padding='same', activation='relu')(x1)
    x1 = tf.keras.layers.BatchNormalization()(x1)    
    x1 = tf.keras.layers.Conv2D(128, 3, padding='same', activation='relu')(x1)
    x1= tf.keras.layers.BatchNormalization()(x1)
        
    x2 = tf.keras.layers.MaxPooling2D(padding='same')(x1)
    
    x2 = tf.keras.layers.Conv2D(256, 3, padding='same', activation='relu')(x2)
    x2 = tf.keras.layers.BatchNormalization()(x2)    
    x2 = tf.keras.layers.Conv2D(256, 3, padding='same', activation='relu')(x2)
    x2= tf.keras.layers.BatchNormalization()(x2)
    
    x3 = tf.keras.layers.MaxPooling2D(padding='same')(x2)
    
    x3 = tf.keras.layers.Conv2D(512, 3, padding='same', activation='relu')(x3)
    x3 = tf.keras.layers.BatchNormalization()(x3)    
    x3 = tf.keras.layers.Conv2D(512, 3, padding='same', activation='relu')(x3)
    x3= tf.keras.layers.BatchNormalization()(x3)
    
    x4 = tf.keras.layers.MaxPooling2D(padding='same')(x3)
    
    x4 = tf.keras.layers.Conv2D(1024, 3, padding='same', activation='relu')(x4)
    x4 = tf.keras.layers.BatchNormalization()(x4)    
    x4 = tf.keras.layers.Conv2D(1024, 3, padding='same', activation='relu')(x4)
    x4= tf.keras.layers.BatchNormalization()(x4)

    x5 = tf.keras.layers.Conv2DTranspose(512, 2, strides=2, padding='same', activation='relu')(x4)
    x5 = tf.keras.layers.BatchNormalization()(x5)

    x6 = tf.concat([x3, x5], axis=-1)
    
    x6 = tf.keras.layers.Conv2D(512, 3, padding='same', activation='relu')(x6)
    x6 = tf.keras.layers.BatchNormalization()(x6)    
    x6 = tf.keras.layers.Conv2D(512, 3, padding='same', activation='relu')(x6)
    x6= tf.keras.layers.BatchNormalization()(x6)
    
    x7= tf.keras.layers.Conv2DTranspose(256, 2, strides=2, padding='same', activation='relu')(x6)
    x7 = tf.keras.layers.BatchNormalization()(x7)

    x8 = tf.concat([x2, x7], axis=-1)  
    
    x8 = tf.keras.layers.Conv2D(256, 3, padding='same', activation='relu')(x8)
    x8 = tf.keras.layers.BatchNormalization()(x8)    
    x8 = tf.keras.layers.Conv2D(256, 3, padding='same', activation='relu')(x8)
    x8= tf.keras.layers.BatchNormalization()(x8)
    
    x9= tf.keras.layers.Conv2DTranspose(128, 2, strides=2, padding='same', activation='relu')(x8)
    x9 = tf.keras.layers.BatchNormalization()(x9)

    x10 = tf.concat([x1, x9], axis=-1)
    
    x10 = tf.keras.layers.Conv2D(128, 3, padding='same', activation='relu')(x10)
    x10 = tf.keras.layers.BatchNormalization()(x10)    
    x10 = tf.keras.layers.Conv2D(128, 3, padding='same', activation='relu')(x10)
    x10 = tf.keras.layers.BatchNormalization()(x10)
   
    
    x11= tf.keras.layers.Conv2DTranspose(64, 2, strides=2, padding='same',
                                        activation='relu')(x10)
    x11 = tf.keras.layers.BatchNormalization()(x11)

    x11 = tf.concat([x, x11], axis=-1)
    
    x12 = tf.keras.layers.Conv2D(64, 3, padding='same', activation='relu')(x11)
    x12 = tf.keras.layers.BatchNormalization()(x12)    
    x12 = tf.keras.layers.Conv2D(64, 3, padding='same', activation='relu')(x12)
    x12 = tf.keras.layers.BatchNormalization()(x12)
    
    output = tf.keras.layers.Conv2D(34, 1, padding='same', activation='softmax')(x12)
    
    return tf.keras.Model(inputs=inputs, outputs=output)

model = create_model()
model.summary()

class MeanIoU(tf.keras.metrics.MeanIoU):
    def update_state(self, y_true, y_pred, sample_weight=None):
        y_pred = tf.argmax(y_pred, axis=-1)
        return super().update_state(y_true, y_pred, sample_weight)

model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['acc', MeanIoU(num_classes=34)])

reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.1, patience=6, verbose=1)

early = EarlyStopping(monitor='val_loss', min_delta=0, patience=15, verbose=1, mode='auto')

filepath = '/content/unet_cityscapes.h5'
checkpoint = ModelCheckpoint(filepath, monitor='val_loss', verbose=1, save_best_only=True, save_weights_only=False, mode='auto')

history = model.fit(dataset_train, epochs=EPOCHS, 
                   steps_per_epoch=train_step_per_epoch,
                   validation_steps=val_step_per_epoch,
                   validation_data=dataset_val, callbacks=[reduce_lr, checkpoint])

loss = history.history['loss']
val_loss = history.history['val_loss']

epochs = range(EPOCHS)
plt.figure()
plt.plot(epochs, loss, 'r', label='Training loss')
plt.plot(epochs, val_loss, 'b', label='Validation loss')
plt.title('Training and Validation Loss')
plt.xlabel('Epoch')
plt.ylabel('Loss Value')
plt.legend()
plt.show()

num = 3

for img, label in dataset_val.take(1):
    pred_label = model.predict(img)
    pred_label = tf.argmax(pred_label, axis=-1)
    pred_label = pred_label[..., tf.newaxis]
    
    plt.figure(figsize=(10, 10))
    for i in range(num):
        print(num)
        plt.subplot(num, 3, i*num+1)
        plt.imshow(tf.keras.preprocessing.image.array_to_img(img[i]))
        plt.subplot(num, 3, i*num+2)
        plt.imshow(tf.keras.preprocessing.image.array_to_img(label[i]))
        plt.subplot(num, 3, i*num+3)
        plt.imshow(tf.keras.preprocessing.image.array_to_img(pred_label[i]))

for img, label in dataset_train.take(1):
    pred_label = model.predict(img)
    pred_label = tf.argmax(pred_label, axis=-1)
    pred_label = pred_label[..., tf.newaxis]
    
    plt.figure(figsize=(10, 10))
    for i in range(num):
        plt.subplot(num, 3, i*num+1)
        plt.imshow(tf.keras.preprocessing.image.array_to_img(img[i]))
        plt.subplot(num, 3, i*num+2)
        plt.imshow(tf.keras.preprocessing.image.array_to_img(label[i]))
        plt.subplot(num, 3, i*num+3)
        plt.imshow(tf.keras.preprocessing.image.array_to_img(pred_label[i]))
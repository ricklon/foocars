import os
import math
import numpy as np
import h5py
import glob
import scipy
import scipy.misc

import serial

import keras
from keras.models import Sequential, Model
from keras.layers.core import Dense, Dropout, Activation, Flatten, Reshape
from keras.layers import Embedding, Input, merge, ELU
from keras.layers.recurrent import SimpleRNN, LSTM
from keras.layers.convolutional import Convolution2D, MaxPooling2D
from keras.optimizers import SGD, Adam, RMSprop
from keras.regularizers import l2, activity_l2, l1
from keras.utils.np_utils import to_categorical
from keras import backend as K
import sklearn.metrics as metrics

import datetime

import pygame
import pygame.camera
from pygame.locals import *
pygame.init()
pygame.camera.init()

debug = True

# setup model
ndata = 0
imgsize = 64
# frame size
nrows = 64
ncols = 64
wr = 0.00001
dp = 0.

# speed, accel, distance, angle
real_in = Input(shape=(2,), name='real_input')

# video frame in, grayscale
frame_in = Input(shape=(3,nrows,ncols), name='img_input')

# convolution for image input
conv1 = Convolution2D(6,3,3,border_mode='same', W_regularizer=l1(wr), init='lecun_uniform')
conv_l1 = conv1(frame_in)
Econv_l1 = ELU()(conv_l1)
pool_l1 = MaxPooling2D(pool_size=(2,2))(Econv_l1)

conv2 = Convolution2D(8,3,3,border_mode='same', W_regularizer=l1(wr), init='lecun_uniform')
conv_l2 = conv2(pool_l1)
Econv_l2 = ELU()(conv_l2)
pool_l2 = MaxPooling2D(pool_size=(2,2))(Econv_l2)
drop_l2 = Dropout(dp)(pool_l2)

conv3 = Convolution2D(16,3,3,border_mode='same', W_regularizer=l1(wr), init='lecun_uniform')
conv_l3 = conv3(drop_l2)
Econv_l3 = ELU()(conv_l3)
pool_l3 = MaxPooling2D(pool_size=(2,2))(Econv_l3)

drop_l3 = Dropout(dp)(pool_l3)

flat = Flatten()(drop_l3)

M = merge([flat,real_in], mode='concat', concat_axis=1)

D1 = Dense(32,W_regularizer=l1(wr), init='lecun_uniform')(M)
ED1 = ELU()(D1)
DED1 = Dropout(dp)(ED1)

S1 = Dense(64,W_regularizer=l1(wr), init='lecun_uniform')(DED1)
ES1 = ELU()(S1)

Steer_out = Dense(1, activation='linear', name='steer_out', init='lecun_uniform')(ES1)

model = Model(input=[real_in, frame_in], output=[Steer_out])

adam = Adam(lr=0.001)


model.compile(loss=['mse'],
              optimizer=adam,
              metrics=['mse'])


# load model weights
model.load_weights('/home/ubuntu/proj/autonomous/steer_only_current.h5')

# initialize webcam
cams = pygame.camera.list_cameras()
cam = pygame.camera.Camera(cams[0],(64,64),'RGB')
cam.start()

# make serial connection
if not debug:
    ser = serial.Serial('/dev/tty.usbmodem1411')
else:
    ser = open('/home/ubuntu/proj/autonomous/test_data.csv')

# initialize speeds
speeds = np.zeros(3,dtype=np.float32)

# Start the loop 
start = datetime.datetime.now()

# function for output string
def drive_str(steer, direction=1, speed=255, ms=0):
    '''Generate string to drive car to send over serial connection
    Format is:
    Steering (0-255 is L/R), Direction (0/1 for rev/forwar), Speed (0 brake, 255 full throttle), time in ms
    Str will look like:
    127,1,255,12345
    '''
    return '{0},{1},{2},{3}'.format(int(steer),int(direction),int(speed),int(ms))

def do_loop():
    global speeds
    # get image as numpy array
    img = pygame.surfarray.array3d(cam.get_image())
    # throw away non-square sides (left and rightmost 20 cols)
    img = img[20:140]
    # Shrink to 64x64
    img = scipy.misc.imresize(img,(64,64),'cubic','RGB').transpose(2,0,1)
    # Read acceleration information (and time, TODO)
    d = ser.readline()
    data = list(map(float,d.strip().split(',')))
    # save some info
    print('Saw {0}'.format(data), end='')
    accel = np.array(data[:3],dtype=np.float32)
    accel[2] -= 1 # subtract accel due to gravity, maybe the car can fly :p
    # update speeds, assume one "time unit" or multiply by elapsed ms
    speeds = speeds + accel
    # compute magnitude of speed and accel
    mspeed = np.sqrt(np.sum(speeds*speeds))
    maccel = np.sqrt(np.sum(accel*accel))
    # rescale inputs ( decide on max speed and accel of vehicle), clamp values to these
    # TODO
    # make prediction
    pred = model.predict([np.array([[mspeed,maccel]]),np.array([img])])
    # rescale output steering
    steer_p = int(255-255*pred[0])
    # get time in ms
    now = datetime.datetime.now()
    t = int((now-start).total_seconds()*1000)
    # create str
    s = drive_str(steer_p,ms=t)
    print(' send {0}'.format(s))
    if not debug:
        ser.write(s)


while True:
    do_loop()
# cleanup
ser.close()
cam.stop()

FROM resin/rpi-raspbian:jessie

RUN apt-get update && apt-get install -y --no-install-recommends \
  apt-utils wget unzip build-essential cmake pkg-config \
  libjpeg-dev libtiff5-dev libjasper-dev libpng12-dev \
  libavcodec-dev libavformat-dev libswscale-dev libv4l-dev \
  libxvidcore-dev libx264-dev \
  libgtk2.0-dev libgtk-3-dev \
  libatlas-base-dev gfortran \
  python3-dev python3-pip python-pip python3-h5py \
  python3-numpy python3-matplotlib python3-scipy python3-pandas 

WORKDIR autonomous

COPY . .

# https://github.com/samjabrahams/tensorflow-on-raspberry-pi/releases
RUN wget https://github.com/samjabrahams/tensorflow-on-raspberry-pi/releases/download/v1.1.0/tensorflow-1.1.0-cp34-cp34m-linux_armv7l.whl
# RUN cp  tensorflow-1.1.0-cp34-cp34m-linux_armv7l.whl  tensorflow-1.1.0-cp35-cp35m-linux_armv7l.whl

RUN pip3 install  tensorflow-1.1.0-cp34-cp34m-linux_armv7l.whl 

RUN pip3 install mock


# Enable command line Arduino via platformio
RUN pip install platformio
# Enable pic32 compiler execution
RUN ln -s /lib/arm-linux-gnueabihf/ld-linux.so.3 /lib/ld-linux.so.3
RUN pio platform install microchippic32

# Enable and compile a default program
WORKDIR /autonomous/arduino/MOTTOServoDataSampleDelay
RUN pio lib install 944
RUN pio run
RUN pio device list 

WORKDIR /autonomous
RUN pip3 install -r requirements.txt

# This section is being replaced because Docker and Systemd don't work easily togeter.
# Instead we'll run ottoMicrologger.py directly
# Set up the raspberry pi services
#WORKDIR /usr/local/bin
#RUN ln -s /autonomous/services/ottoMicroLogger.py
#RUN ln -s /autonomous/services/ottoMicroLogger.service
#RUN systemctl enable /autonomous/services/ottoMicroLogger.service

# TODO: Enable USB Flash drive code
# TODO: doccker command to upload Arduino code to car

# TODO: add default weigths
# TODO: Run ottoMicrologger.py upon running the car docker


RUN echo  "Done"

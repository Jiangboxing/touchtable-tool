# Use an official Python runtime as a parent image
FROM python:3.6.8-alpine3.9

# Install packages
RUN   apk update && \
      apk add python3-dev \
      build-base \
      gfortran file binutils \
      openblas-dev \
      libstdc++ openblas \
      openssh \
      openssh-keygen \
      git \
      libzmq \
      zeromq-dev 
      
RUN pip3 install zmq 
RUN pip3 install numpy
RUN pip3 install scipy
RUN pip3 install scikit-learn
RUN pip3 install astral pytz eve requests

# Create an ssh key
RUN ssh-keygen -q -t rsa -N '' -f /root/.ssh/id_rsa
RUN cat ~/.ssh/id_rsa.pub

WORKDIR /app/demkit

# Copy the sources that we require
COPY components /app/demkit/components
COPY conf /app/demkit/conf
COPY tmp /app/demkit/tmp
COPY tools /app/demkit/tools
COPY demkit.py /app/demkit/
COPY docker /app/demkit/docker
COPY .git /app/demkit/.git

RUN mkdir /zmq
RUN mkdir /app/workspace
RUN mkdir /scripts

WORKDIR /app/demkit/docker

# # Do some other things like copying the config internally
RUN cp -f usrconf.py ../conf

WORKDIR /app/demkit/docker/scripts
RUN cp -Rf * /scripts

WORKDIR /app/demkit/
RUN rm -Rf docker

# # Now setup DEMKit itself
WORKDIR /app/demkit

# Finally export everything
VOLUME /app/workspace
VOLUME /root/.ssh

# Set the default environment variables
ENV DEMKIT_FOLDER=example
ENV DEMKIT_MODEL=demohouse
ENV DEMKIT_COMPONENTS=/app/demkit/components/

ENV DEMKIT_INFLUXURL=http//influx
ENV DEMKIT_INFLUXPORT=8068
ENV DEMKIT_INFLUXDB=dem

ENV PATH "$PATH:/scripts"

# Run app.py when the container launches
CMD sh /scripts/autoexec.sh

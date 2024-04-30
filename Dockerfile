# Use Ubuntu runtime as the base image
FROM ubuntu:22.04

# Set the working directory in the container
WORKDIR /app

# Install Python, pip, wget, and tar and set Python 3 as the default Python version
RUN apt-get update && \
    apt-get install -y python3 python3-pip wget tar && \
    rm -f /usr/bin/python && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    rm -f /usr/bin/pip && \
    ln -s /usr/bin/pip3 /usr/bin/pip

# Copy the requirements file to the working directory
COPY requirements.txt .

# Install requirements
RUN pip install --no-cache-dir -r requirements.txt

# Install PyTorch (adjust the command based on your system and CUDA version)
RUN pip install torch

# Download and install IPFS 
# NOTE: Pick the arm64 or amd64 version depending on your architecture
RUN wget https://dist.ipfs.tech/kubo/v0.28.0/kubo_v0.28.0_linux-arm64.tar.gz && \
    tar -xvzf kubo_v0.28.0_linux-arm64.tar.gz && \
    cd kubo && \
    ./install.sh

# Initialize IPFS
RUN ipfs init

# Copy the rest of the application code to the working directory
COPY . .

# Expose the Docker socket file & port
VOLUME /var/run/docker.sock:/var/run/docker.sock
EXPOSE 8000
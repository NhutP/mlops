#!/bin/bash

cd ~
URL="https://download.redis.io/redis-stable.tar.gz"
FILENAME=$(basename "$URL")
DIRNAME="${FILENAME%.tar.gz}"  # Remove .tgz extension to get directory name

# Download the file if it does not exist
if [ ! -f "$FILENAME" ]; then
    wget -c "$URL" -O "$FILENAME"
    
    # Ensure download was successful before proceeding
    if [ $? -ne 0 ]; then
        rm -f "$FILENAME"  # Remove partial file if download failed
        exit 1
    fi
fi

# Extract the file if not already extracted
if [ ! -d "$DIRNAME" ]; then
    tar -xzvf "$FILENAME"
    apt update
    apt install build-essential -y
    cd redis-stable
    make
    make distclean      # Clean previous build artifacts
    make BUILD_TLS=yes
    make install
fi

# sysctl vm.overcommit_memory=1

# apt update
# apt install redis-tools -y

# cd redis-stable
# make BUILD_TLS=yes
# make install


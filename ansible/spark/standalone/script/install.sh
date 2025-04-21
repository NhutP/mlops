#!/bin/bash

cd ~
URL="https://dlcdn.apache.org/spark/spark-3.5.5/spark-3.5.5-bin-hadoop3.tgz"
FILENAME=$(basename "$URL")
DIRNAME="${FILENAME%.tgz}"  # Remove .tgz extension to get directory name

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
    tar -xzf "$FILENAME"
fi

# cd ./spark-3.5.4-bin-hadoop3
# ./sbin/start-master.sh --host  --port 7077 --webui-port 8080
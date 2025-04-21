#!/bin/bash

cd ~
URL="https://packages.confluent.io/archive/7.9/confluent-7.9.0.zip"

FILENAME=$(basename "$URL")
DIRNAME="${FILENAME%.zip}"  # Remove .tgz extension to get directory name

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
    unzip "$FILENAME"
fi

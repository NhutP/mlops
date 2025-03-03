#!/bin/bash

# Install dependencies and Redis automatically without prompts
apt-get update -y
apt-get install -y lsb-release curl gpg

# Add Redis repository
curl -fsSL https://packages.redis.io/gpg | gpg --dearmor -o /usr/share/keyrings/redis-archive-keyring.gpg
chmod 644 /usr/share/keyrings/redis-archive-keyring.gpg

echo "deb [signed-by=/usr/share/keyrings/redis-archive-keyring.gpg] https://packages.redis.io/deb $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/redis.list

# Update package lists and install Redis automatically
apt-get update -y
apt-get install -y redis
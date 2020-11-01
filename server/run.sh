#!/bin/sh

# Assign an IP address to local loopback
ifconfig lo 127.0.0.1

# Add a hosts record, pointing API endpoint to local loopback
echo "127.0.0.1   kms.us-east-1.amazonaws.com" >> /etc/hosts

# Run traffic forwarder in background and start the server
nohup python3 /app/traffic-forwarder.py 443 3 8000 &
python3 /app/server.py
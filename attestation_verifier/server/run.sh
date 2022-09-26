#!/bin/sh

# Assign an IP address to local loopback
ifconfig lo 127.0.0.1

# Add a hosts record, pointing API endpoint to local loopback
echo "127.0.0.1   nitro-enclaves-demo.richardfan.xyz" >> /etc/hosts

# Run traffic forwarder in background and start the app
nohup python3 /app/traffic-forwarder.py 80 3 8000 &
python3 /app/server.py

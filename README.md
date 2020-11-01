
# AWS Nitro Enclaves Python demo

**WARNING: This project is just proof-of-concept, not production-ready, use at your own risk.**

This project showcase how we can use Python socket package to establish communication between EC2 instance and Nitro Enclave. And use a proxy to make HTTPS call from inside the enclave as usual.

## Architecture

See [Architecture diagram](https://github.com/richardfan1126/nitro-enclave-python-demo/blob/master/docs/architecture.md)

## Installation guide

TBD

## File structure

 - `client/`

    This directory contains the code running on parent EC2 instance. Use `requirements.txt` to install necessary pip package
 
 - `server/Dockerfile`

   This file is to build the eif file required to run on the Nitro Enclave.

 - `server/server.py`

   This is the main server app

 - `server/traffic-forwarder.py`

   This is a background app running on Nitro Enclave to forward HTTP traffic between parent instance and enclave via the vsock

 - `server/run.sh`
 
   This is the bootstrap shell script. It first modify the Nitro Enclave netwrok config to assign an IP address `127.0.0.1` to local loopback. Then start the traffic forwarder and the main server app



## Todos

 - Write the installation guide
 - Add implementation of attestation
 
License
----

Apache License, Version 2.0
#!/bin/bash

rm nitro-enclave-python-demo.eif
docker rmi -f $(docker images -a -q)
nitro-cli build-enclave --docker-dir ./ --docker-uri richardfan1126/nitro-enclave-python-demo:latest --output-file nitro-enclave-python-demo.eif

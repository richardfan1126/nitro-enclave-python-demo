#!/bin/bash

rm nitro-enclave-python-demo.eif
docker rmi -f $(docker images -a -q)
nitro-cli build-enclave --docker-dir ./ --docker-uri richardfan1126/nitro-enclave-python-demo:latest --output-file nitro-enclave-python-demo.eif
nitro-cli run-enclave --cpu-count 2 --memory 2048 --eif-path nitro-enclave-python-demo.eif --debug-mode
nitro-cli console --enclave-id $(nitro-cli describe-enclaves | jq -r ".[0].EnclaveID")

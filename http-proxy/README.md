
# AWS Nitro Enclaves Python demo - HTTP Proxy

**WARNING: This project is just proof-of-concept, not production-ready, use at your own risk.**

This project showcase how we can use Python socket package to establish communication between EC2 instance and Nitro Enclave. And use a proxy to make HTTPS call from inside the enclave as usual.

## Architecture

See [Architecture diagram](https://github.com/richardfan1126/nitro-enclave-python-demo/blob/master/http-proxy/docs/architecture.md)

## Installation guide

1. Create an EC2 instance with Nitro Enclave enabled. See [AWS documentation](https://docs.aws.amazon.com/enclaves/latest/user/create-enclave.html) for steps and requirement.

   Amazon Linux 2 AMI is recommended.

1. Create a new IAM role for the instance, attach `AWSKeyManagementServicePowerUser` policy to the role.

   See [AWS Documentation](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/iam-roles-for-amazon-ec2.html#working-with-iam-roles) for more detail

1. SSH into the instance. Install `nitro-cli`

   ```
   $ sudo amazon-linux-extras install aws-nitro-enclaves-cli
   $ sudo yum install aws-nitro-enclaves-cli-devel -y
   $ sudo usermod -aG ne $USER
   $ sudo usermod -aG docker $USER
   ```

1. Modify the preallocated memory for the enclave to 2048 MB.

   Modify the file `/etc/nitro_enclaves/allocator.yaml`, change the following line:

   ```
   # memory_mib: 512
   memory_mib: 2048
   ```

1. Enable Docker and Nitro Enclaves Allocator

   ```
   $ sudo systemctl start nitro-enclaves-allocator.service && sudo systemctl enable nitro-enclaves-allocator.service
   $ sudo systemctl start docker && sudo systemctl enable docker
   ```

1. Reboot the instance

1. Loggin to the instance, clone the repository

   ```
   $ git clone https://github.com/richardfan1126/nitro-enclave-python-demo.git
   ```

1. Goto AWS KMS console, and copy a Key ID.

   If you don't have Customer Managed Key, just pick one AWS managed key. It's just for demo purpose

1. Edit `http-proxy/server/server.py`, paste the Key ID into the following line

   ```
   def aws_api_call(credential):
       ...
       response = client.describe_key(
           KeyId = 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx' # Paste the Key ID here
       )
   ```

1. Use the build script to build and run the enclave image

   ```
   $ cd nitro-enclave-python-demo/http-proxy/server
   $ chmod +x build.sh
   $ ./build.sh
   ```

1. After the enclave has launched, you can find the CID of it.

   Find the following line, and take note the `enclave-cid` value

   ```
   Started enclave with enclave-cid: 16, memory: 1024 MiB, cpu-ids: [1, 3]
   ```

1. Open a new SSH session, run the `vsock-proxy` tool

   ```
   $ vsock-proxy 8000 kms.us-east-1.amazonaws.com 443
   ```

1. Open another SSH session, install python3 and the necessary packages for running client app

   ```
   $ yum install python3 -y
   $ cd nitro-enclave-python-demo/http-proxy/client
   $ python3 -m venv venv
   $ source venv/bin/activate
   $ pip install -r requirements.txt
   ```

1. Run the client app, replace `<cid>` with the enclave CID you get in step 11

   ```
   $ python3 client.py <cid>
   ```

1. If everthing is OK, you will see the the key ID and key state are shown on the screen.

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

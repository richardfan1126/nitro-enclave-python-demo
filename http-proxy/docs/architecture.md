# Architecture

This document shows the overall architecture and the data flow of the demo

## Diagram

![Architecture](https://github.com/richardfan1126/nitro-enclave-python-demo/blob/master/docs/assets/Architecture.png)

1. The client app grab the AWS credential from EC2 instance metadata, and send it to the server running in enclave, via the vsock

2. The server app use boto3 to make API call via HTTPS, using the AWS credential provided in step 1.

   The modified `/etc/hosts` file will redirect traffic to local loopback (127.0.0.1)

3. The traffic-forwarder app will forward HTTPS traffic and send it to the parent instance via the vsock tunnel.

4. `vsock-proxy` running in parent instance will forward the vsock traffic as the original HTTPS traffic, and send it out via the ENI.

   It will then forward the HTTPS response back to the enclave via vsock tunnel.

5. The traffic-forwarder app forward the traffic to the server app as HTTPS response.

6. The server app then send the customized result to client app via vsock tunnel.
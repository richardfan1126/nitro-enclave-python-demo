import sys
import socket
import requests
import json
import base64
import subprocess

def get_aws_session_token():
    """
    Get the AWS credential from EC2 instance metadata
    """
    r = requests.get("http://169.254.169.254/latest/meta-data/iam/security-credentials/")
    instance_profile_name = r.text

    r = requests.get("http://169.254.169.254/latest/meta-data/iam/security-credentials/%s" % instance_profile_name)
    response = r.json()

    credential = {
        'access_key_id' : response['AccessKeyId'],
        'secret_access_key' : response['SecretAccessKey'],
        'token' : response['Token']
    }

    return credential

def main():
    # Start vsock-proxy in background process
    vsock_proxy_process = subprocess.Popen(
        [
            'vsock-proxy',
            '8000',
            'kms.us-east-1.amazonaws.com',
            '443'
        ]
    )

    # Get EC2 instance metedata
    credential = get_aws_session_token()

    # Create a vsock socket object
    s = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)
    
    # Get CID from command line parameter
    cid = int(sys.argv[1])

    # Get ciphertext from shell input
    ciphertext = sys.argv[2]

    # The port should match the server running in enclave
    port = 5000

    # Connect to the server
    s.connect((cid, port))

    # Send AWS credential and ciphertext to the server running in enclave
    s.send(str.encode(json.dumps({
        'credential': credential,
        'ciphertext': ciphertext,
    })))
    
    # receive data from the server
    response = json.loads(s.recv(65536).decode())

    plaintext = base64.b64decode(response['Plaintext']).decode()
    print(plaintext)

    # close the connection 
    s.close()

    # Kill the vsock-proxy
    vsock_proxy_process.kill()

if __name__ == '__main__':
    main()

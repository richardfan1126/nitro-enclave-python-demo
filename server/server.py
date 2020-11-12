import socket
import requests
import json
import subprocess

def aws_api_call(credential, ciphertext):
    """
    Make AWS API call using credential obtained from parent EC2 instance
    """

    # Call the standalone kmstool through subprocess
    proc = subprocess.Popen(
        [
            "/app/kmstool_enclave_cli",
            "--region", "us-east-1",
            "--proxy-port", "8000",
            "--aws-access-key-id", "%s" % credential['access_key_id'],
            "--aws-secret-access-key", "%s" % credential['secret_access_key'],
            "--aws-session-token", "%s" % credential['token'],
            "--ciphertext", "%s" % ciphertext,
        ],
        stdout=subprocess.PIPE
    )

    result = proc.communicate()[0]

    # Return some data from API response
    return {
        'Plaintext': result.decode()
    }

def main():
    print("Starting server...")
    
    # Create a vsock socket object
    s = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)

    # Listen for connection from any CID
    cid = socket.VMADDR_CID_ANY

    # The port should match the client running in parent EC2 instance
    port = 5000

    # Bind the socket to CID and port
    s.bind((cid, port))

    # Listen for connection from client
    s.listen()

    while True:
        c, addr = s.accept()

        # Get data sent from parent instance
        payload = c.recv(65536)
        client_request = json.loads(payload.decode())

        credential = client_request['credential']
        ciphertext = client_request['ciphertext']

        # Get data from AWS API call
        content = aws_api_call(credential, ciphertext)

        # Send the response back to parent instance
        c.send(str.encode(json.dumps(content)))

        # Close the connection
        c.close() 

if __name__ == '__main__':
    main()

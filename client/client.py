import sys
import socket
import requests

def get_aws_session_token():
    r = requests.put("http://169.254.169.254/latest/api/token", headers = {
        "X-aws-ec2-metadata-token-ttl-seconds": "21600"
    })
    return r.text

def main():
    aws_token = get_aws_session_token() # Get EC2 instance profile token

    # Create a vsock socket object
    s = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)
    
    cid = int(sys.argv[1])  # Get CID from command line parameter
    port = 5000

    # Connect to the server
    s.connect((cid, port))
    
    # receive data from the server
    print(s.recv(1024).decode())

    # close the connection 
    s.close()

if __name__ == '__main__':
    main()

import sys
import socket
import json

def main():
    # Create a vsock socket object
    s = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)
    
    # Get CID from command line parameter
    cid = int(sys.argv[1])

    # The port should match the server running in enclave
    port = 5000

    # Connect to the server
    s.connect((cid, port))

    # Send command to the server running in enclave
    s.send(str.encode(json.dumps({
        'action': 'connect'
    })))

    # receive the plaintext from the server and print it to console
    response = s.recv(65536)
    print(response.decode())

    # close the connection 
    s.close()

if __name__ == '__main__':
    main()

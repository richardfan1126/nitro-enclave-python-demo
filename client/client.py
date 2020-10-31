import sys
import socket

def main():
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

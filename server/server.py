import socket

def main():
    print("Starting server...")
    
    # Create a vsock socket object
    s = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)

    cid = socket.VMADDR_CID_ANY
    port = 5000

    s.bind((cid, port)) # Bind the socket to CID and port

    # Listen for connection from client
    s.listen()

    while True: 
        c, addr = s.accept()
        c.send(str.encode('Thank you for connecting'))
        c.close() 

if __name__ == '__main__':
    main()

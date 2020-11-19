import socket
import json
import base64

from NsmUtil import NSMUtil

def main():
    print("Starting server...")

    # Initialise NSMUtil
    nsm_util = NSMUtil()
    
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

        # Get command from client
        payload = c.recv(4096)
        request = json.loads(payload.decode())

        if request['action'] == 'connect':
            # Get AWS credential sent from parent instance
            credential = request['credential']

            # Get attestation document
            attestation_doc = nsm_util.get_attestation_doc()

            # Base64 encode the attestation doc
            attestation_doc_b64 = base64.b64encode(attestation_doc).decode()

            # Generate JSON response
            response = json.dumps({
                'attestation_doc_b64': attestation_doc_b64
            })

            # Send the response back to parent instance
            c.sendall(str.encode(response))
        elif request['action'] == 'decrypt':
            # Decode the base64 ciphertext
            ciphertext_b64 = request['ciphertext_b64']
            ciphertext = base64.b64decode(ciphertext_b64)

            # Decrypt ciphertext using private key
            plaintext = nsm_util.decrypt(ciphertext)

            # Send the plaintext back to client
            c.sendall(str.encode(plaintext))

        # Close the connection
        c.close()

if __name__ == '__main__':
    main()

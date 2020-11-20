import socket
import json
import base64

from NsmUtil import NSMUtil

def main():
    print("Starting server...")

    # Initialise NSMUtil
    nsm_util = NSMUtil()
    
    # Create a vsock socket object
    client_socket = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)

    # Listen for connection from any CID
    cid = socket.VMADDR_CID_ANY

    # The port should match the client running in parent EC2 instance
    client_port = 5000

    # Bind the socket to CID and port
    client_socket.bind((cid, client_port))

    # Listen for connection from client
    client_socket.listen()

    while True:
        client_connection, addr = client_socket.accept()

        # Get command from client
        payload = client_connection.recv(4096)
        request = json.loads(payload.decode())

        if request['action'] == 'connect':
            # Get attestation document
            attestation_doc = nsm_util.get_attestation_doc()

            # Base64 encode the attestation doc
            attestation_doc_b64 = base64.b64encode(attestation_doc).decode()

            # Create a vsock socket object for connection to datastore
            datastore_socket = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)
            
            # Parent CID is always 3
            datastore_cid = 3

            # The port should match the datastore
            data_store_port = 6000

            # Connect to the server
            datastore_socket.connect((datastore_cid, data_store_port))

            # Generate JSON response
            datastore_request = json.dumps({
                'attestation_doc_b64': attestation_doc_b64
            })

            # Send the attestation document to datastore
            datastore_socket.send(str.encode(datastore_request))

            # Receive response from datastore
            datastore_response = datastore_socket.recv(65536)
            datastore_response_obj = json.loads(datastore_response.decode())

            # Check if datastore request succeed
            if datastore_response_obj['success']:
                # Decode the base64 ciphertext
                ciphertext_b64 = datastore_response_obj['ciphertext_b64']
                ciphertext = base64.b64decode(ciphertext_b64)

                # Decrypt ciphertext using private key
                plaintext = nsm_util.decrypt(ciphertext)

                # Send the plaintext back to client
                client_connection.sendall(str.encode(plaintext))
            else:
                # Send the error message to client
                err_msg = datastore_response_obj['error']
                client_connection.sendall(str.encode(err_msg))

            # Close connection with datastore
            datastore_socket.close()

        # Close the connection with client
        client_connection.close()

if __name__ == '__main__':
    main()

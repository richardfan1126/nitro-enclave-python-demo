import socket
import json
import base64
import requests

from NsmUtil import NSMUtil

def strip_credit_card_no(records):
    processed_records = []

    for record in records:
        processed_records.append({
            "name": record["name"],
            "credit_card_no_last_4_digit": record["credit_card_no"][-4:]
        })
    
    return processed_records

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
            # Generate attestation document
            attestation_doc = nsm_util.get_attestation_doc()

            # Base64 encode the attestation doc
            attestation_doc_b64 = base64.b64encode(attestation_doc).decode()

            # Generate JSON request
            secretstore_request = {
                'attestation_doc': attestation_doc_b64
            }

            # Send API request to the secretstore
            r = requests.post("http://nitro-enclaves-demo.richardfan.xyz", json = secretstore_request)
            secretstore_response_obj = r.json()

            # Check if secretstore request succeed
            if secretstore_response_obj['success']:
                # Decode the base64 ciphertext
                ciphertext_bundle = secretstore_response_obj['ciphertext_bundle']

                # Decrypt ciphertext using private key
                plaintext = nsm_util.decrypt(ciphertext_bundle)

                records = strip_credit_card_no(json.loads(plaintext))

                # Send the plaintext back to client
                client_connection.sendall(str.encode(json.dumps(records)))
            else:
                # Send the error message to client
                err_msg = secretstore_response_obj['error']
                client_connection.sendall(str.encode(err_msg))

        # Close the connection with client
        client_connection.close()

if __name__ == '__main__':
    main()

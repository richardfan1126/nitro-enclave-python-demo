import sys
import socket
import json
import base64

from attestation_verifier import verify_attestation_doc, encrypt

def main():
    # Create a vsock socket object
    s = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)

    # Listen for connection from any CID
    cid = socket.VMADDR_CID_ANY

    # The port for communicating with server running in enclave, should match the server config
    port = 6000

    # Bind the socket to CID and port
    s.bind((cid, port))

    # Listen for connection from enclave server
    s.listen()

    print("SecretStore running...")

    while True:
        c, addr = s.accept()

        # Get command from enclave server
        payload = c.recv(65536)
        request = json.loads(payload.decode())

        # Get attestation document
        attestation_doc_b64 = request['attestation_doc_b64']
        attestation_doc = base64.b64decode(attestation_doc_b64)

        # Get the root cert PEM content
        with open('root.pem', 'r') as file:
            root_cert_pem = file.read()

        # Get PCR0 from command line parameter
        pcr0 = sys.argv[1]

        # Verify attestation document
        try:
            verify_attestation_doc(attestation_doc, pcrs = [pcr0], root_cert_pem = root_cert_pem)
        except Exception as e:
            # Send error response back to enclave
            response_to_enclave = {
                'success': False,
                'error': str(e)
            }
        else:
            # This is the secret requested
            secret = "Hello World"

            # Generate encrypted response using public key in attestation document
            ciphertext_b64 = encrypt(attestation_doc, secret)

            # Send the result back to enclave
            response_to_enclave = {
                'success': True,
                'ciphertext_b64': ciphertext_b64
            }

        # Send respond back to enclave
        c.sendall(str.encode(json.dumps(response_to_enclave)))

        # Close the connection
        c.close()

if __name__ == '__main__':
    main()

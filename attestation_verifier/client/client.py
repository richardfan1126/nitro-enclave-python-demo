import sys
import socket
import requests
import json
import base64

from attestation_verifier import verify_attestation_doc, encrypt

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
    # Get EC2 instance metedata
    credential = get_aws_session_token()

    # Create a vsock socket object
    s = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)
    
    # Get CID from command line parameter
    cid = int(sys.argv[1])

    # The port should match the server running in enclave
    port = 5000

    # Connect to the server
    s.connect((cid, port))

    # Send AWS credential to the server running in enclave
    s.send(str.encode(json.dumps({
        'action': 'connect',
        'credential': credential
    })))
    
    # receive data from the server
    response = s.recv(65536)

    # close the connection 
    s.close()

    # Conver JSON string to object
    response_obj = json.loads(response.decode())

    # Get attestation document
    attestation_doc_b64 = response_obj['attestation_doc_b64']
    attestation_doc = base64.b64decode(attestation_doc_b64)

    # Get the root cert PEM content
    with open('root.pem', 'r') as file:
        root_cert_pem = file.read()

    # Get PCR0 from command line parameter
    pcr0 = sys.argv[2]

    # Verify attestation document
    try:
        verify_attestation_doc(attestation_doc, pcrs = [pcr0], root_cert_pem = root_cert_pem)
    except Exception as e:
        print(e)
    else:
        # Generate encrypted response using public key in attestation document
        ciphertext_b64 = encrypt(attestation_doc, "Hello World")

        # Create another new vsock socket object
        s = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)

        # Connect to the server
        s.connect((cid, port))

        # Send the response back to enclave
        response_to_enclave = {
            'action': 'decrypt',
            'ciphertext_b64': ciphertext_b64
        }
        s.send(str.encode(json.dumps(response_to_enclave)))
        
        # receive the plaintext from the server and print it to console
        response = s.recv(65536)
        print(response.decode())

        # close the connection 
        s.close()

if __name__ == '__main__':
    main()

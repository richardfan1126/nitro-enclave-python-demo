import cbor2
import cose
import base64
import json

from cose import EC2, CoseAlgorithms, CoseEllipticCurves
from Crypto.Util.number import long_to_bytes
from Crypto.Random import get_random_bytes
from OpenSSL import crypto

from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256


def verify_attestation_doc(attestation_doc, pcrs = {}, root_cert_pem = None):
    """
    Verify the attestation document
    If invalid, raise an exception
    """
    # Decode CBOR attestation document
    data = cbor2.loads(attestation_doc)

    # Load and decode document payload
    doc = data[2]
    doc_obj = cbor2.loads(doc)

    # Get PCRs from attestation document
    document_pcrs_arr = doc_obj['pcrs']

    # Get signing certificate from attestation document
    cert = crypto.load_certificate(crypto.FILETYPE_ASN1, doc_obj['certificate'])

    print("Received request from enclave with PCR0: {}".format(document_pcrs_arr[0].hex()))

    ##############################################
    # Part 1: Validating signing certificate PKI #
    ##############################################
    if root_cert_pem is not None:
        # Create an X509Store object for the CA bundles
        store = crypto.X509Store()

        # Create the CA cert object from PEM string, and store into X509Store
        _cert = crypto.load_certificate(crypto.FILETYPE_PEM, root_cert_pem)
        store.add_cert(_cert)

        # Get the CA bundle from attestation document and store into X509Store
        # Except the first certificate, which is the root certificate
        for _cert_binary in doc_obj['cabundle'][1:]:
            _cert = crypto.load_certificate(crypto.FILETYPE_ASN1, _cert_binary)
            store.add_cert(_cert)

        # Get the X509Store context
        store_ctx = crypto.X509StoreContext(store, cert)
        
        # Validate the certificate
        # If the cert is invalid, it will raise exception
        store_ctx.verify_certificate()

    ################################
    # Part 2: Validating signature #
    ################################
    
    # Get the key parameters from the cert public key
    cert_public_numbers = cert.get_pubkey().to_cryptography_key().public_numbers()
    x = cert_public_numbers.x
    y = cert_public_numbers.y
    curve = cert_public_numbers.curve

    x = long_to_bytes(x)
    y = long_to_bytes(y)

    # Create the EC2 key from public key parameters
    key = EC2(alg = CoseAlgorithms.ES384, x = x, y = y, crv = CoseEllipticCurves.P_384)

    # Get the protected header from attestation document
    phdr = cbor2.loads(data[0])

    # Construct the Sign1 message
    msg = cose.Sign1Message(phdr = phdr, uhdr = data[1], payload = doc)
    msg.signature = data[3]

    # Verify the signature using the EC2 key
    if not msg.verify_signature(key):
        raise Exception("Wrong signature")

    ###########################
    # Part 3: Validating PCRs #
    ###########################
    for index in pcrs:
        pcr = pcrs[index]
        
        # Attestation document doesn't have specified PCR, raise exception
        if index not in document_pcrs_arr or document_pcrs_arr[index] is None:
            raise Exception("Wrong PCR%s" % index)

        # Get PCR hexcode
        doc_pcr = document_pcrs_arr[index].hex()

        # Check if PCR match
        if pcr != doc_pcr:
            raise Exception("Wrong PCR%s" % index)

    return

def encrypt(attestation_doc, plaintext):
    """
    Encrypt message using public key in attestation document
    """

    # Decode CBOR attestation document
    data = cbor2.loads(attestation_doc)

    # Load and decode document payload
    doc = data[2]
    doc_obj = cbor2.loads(doc)

    # Get the public key from attestation document
    public_key_byte = doc_obj['public_key']
    public_key = RSA.import_key(public_key_byte)

    # Generate a random session for data encryption
    session_key = get_random_bytes(32)

    # Encrypt the session key with the public RSA key
    cipher_rsa = PKCS1_OAEP.new(public_key, SHA256)
    enc_session_key = cipher_rsa.encrypt(session_key)

    # Encrypt the data with the AES session key
    nonce = get_random_bytes(12)
    cipher_aes = AES.new(session_key, AES.MODE_GCM, nonce = nonce)
    ciphertext, digest = cipher_aes.encrypt_and_digest(str.encode(plaintext))

    # Return the encrypted session key, nonce, tag and ciphertext
    return "{}:{}:{}".format(
        base64.b64encode(enc_session_key).decode(),
        base64.b64encode(cipher_aes.nonce).decode(),
        base64.b64encode(ciphertext + digest).decode(),
    )

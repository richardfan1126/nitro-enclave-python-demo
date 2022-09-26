"""
This file is modified based on donkersgoed's repository (https://github.com/donkersgoed/nitropepper-enclave-app)
"""

import base64
import json

import Crypto
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP, AES

import libnsm

class NSMUtil():
    """NSM util class."""

    def __init__(self):
        """Construct a new NSMUtil instance."""
        # Initialize the Rust NSM Library
        self._nsm_fd = libnsm.nsm_lib_init() # pylint:disable=c-extension-no-member
        # Create a new random function `nsm_rand_func`, which
        # utilizes the NSM module.
        self.nsm_rand_func = lambda num_bytes : libnsm.nsm_get_random( # pylint:disable=c-extension-no-member
            self._nsm_fd, num_bytes
        )

        # Force pycryptodome to use the new rand function.
        # Without this, pycryptodome defaults to /dev/random
        # and /dev/urandom, which are not available in Enclaves.
        self._monkey_patch_crypto(self.nsm_rand_func)

        # Generate a new RSA certificate, which will be used to
        # generate the Attestation document and to decrypt results
        # for KMS Decrypt calls with this document.
        self._rsa_key = RSA.generate(2048)
        self._public_key = self._rsa_key.publickey().export_key('DER')

    def get_attestation_doc(self):
        """Get the attestation document from /dev/nsm."""
        libnsm_att_doc_cose_signed = libnsm.nsm_get_attestation_doc( # pylint:disable=c-extension-no-member
            self._nsm_fd,
            self._public_key,
            len(self._public_key)
        )
        return libnsm_att_doc_cose_signed
    
    def decrypt(self, ciphertext_bundle):
        """
        Decrypt ciphertext using private key
        """

        private_key = self._rsa_key
        ciphertext_bundle = json.loads(ciphertext_bundle)

        enc_session_key = ciphertext_bundle[0]
        nonce = ciphertext_bundle[1]
        tag = ciphertext_bundle[2]
        ciphertext = ciphertext_bundle[3]

        enc_session_key = base64.b64decode(enc_session_key)
        nonce = base64.b64decode(nonce)
        tag = base64.b64decode(tag)
        ciphertext = base64.b64decode(ciphertext)

        # Decrypt the session key with the private RSA key
        cipher_rsa = PKCS1_OAEP.new(private_key)
        session_key = cipher_rsa.decrypt(enc_session_key)

        # Decrypt the data with the AES session key
        cipher_aes = AES.new(session_key, AES.MODE_EAX, nonce)
        plaintext = cipher_aes.decrypt_and_verify(ciphertext, tag)

        return plaintext.decode()

    @classmethod
    def _monkey_patch_crypto(cls, nsm_rand_func):
        """Monkeypatch Crypto to use the NSM rand function."""
        Crypto.Random.get_random_bytes = nsm_rand_func
        def new_random_read(self, n_bytes): # pylint:disable=unused-argument
            return nsm_rand_func(n_bytes)
        Crypto.Random._UrandomRNG.read = new_random_read # pylint:disable=protected-access

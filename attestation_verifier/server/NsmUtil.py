"""
This file is modified based on donkersgoed's repository (https://github.com/donkersgoed/nitropepper-enclave-app)
"""

import base64

import Crypto
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

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
    
    def decrypt(self, ciphertext):
        """
        Decrypt ciphertext using private key
        """
        cipher = PKCS1_OAEP.new(self._rsa_key)
        plaintext = cipher.decrypt(ciphertext)

        return plaintext.decode()

    @classmethod
    def _monkey_patch_crypto(cls, nsm_rand_func):
        """Monkeypatch Crypto to use the NSM rand function."""
        Crypto.Random.get_random_bytes = nsm_rand_func
        def new_random_read(self, n_bytes): # pylint:disable=unused-argument
            return nsm_rand_func(n_bytes)
        Crypto.Random._UrandomRNG.read = new_random_read # pylint:disable=protected-access
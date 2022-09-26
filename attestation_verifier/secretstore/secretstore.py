import json
import os
import base64

from fastapi import FastAPI
from pydantic import BaseModel

from attestation_verifier import verify_attestation_doc, encrypt

SECRET = [
    {
        "name": "Ronan Munro",
        "credit_card_no": "4087732854932734"
    },
    {
        "name": "Kai Friduhelm",
        "credit_card_no": "4916098743227612"
    },
    {
        "name": "Gearalt Soraia",
        "credit_card_no": "4556397006192165"
    },
    {
        "name": "Werdheri Ekkebert",
        "credit_card_no": "4716419876002097"
    }
]

class Item(BaseModel):
    attestation_doc: str

app = FastAPI()

@app.post("/")
async def root(item: Item):
    attestation_doc_b64 = item.attestation_doc
    response = main(attestation_doc_b64)
    return response

def main(attestation_doc_b64):
    attestation_doc = base64.b64decode(attestation_doc_b64)

    # Get the root cert PEM content
    with open('root.pem', 'r') as file:
        root_cert_pem = file.read()

    # Get PCR0 from command line parameter
    pcr0 = os.environ.get("PCR0")

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
        secret = json.dumps(SECRET)

        # Generate encrypted response using public key in attestation document
        ciphertext_bundle = encrypt(attestation_doc, secret)

        # Send the result back to enclave
        response_to_enclave = {
            'success': True,
            'ciphertext_bundle': ciphertext_bundle
        }

    return response_to_enclave

from web3 import Web3
import hashlib
import os
from dotenv import load_dotenv

load_dotenv()

RPC_URL = os.getenv("POLYGON_AMOY_RPC_URL")
PRIVATE_KEY = os.getenv("WALLET_PRIVATE_KEY")

w3 = Web3(Web3.HTTPProvider(RPC_URL)) if RPC_URL else None

def get_file_hash(file_data: bytes) -> str:
    sha256_hash = hashlib.sha256()
    sha256_hash.update(file_data)
    return sha256_hash.hexdigest()

def anchor_document_on_chain(doc_sha256: str) -> str:
    if not w3 or not PRIVATE_KEY:
        print("Web3 or Private Key not configured. Skipping on-chain anchoring.")
        return None
        
    if not w3.is_connected():
        print("Web3 is not connected to RPC.")
        return None
        
    try:
        account = w3.eth.account.from_key(PRIVATE_KEY)
        data = w3.to_hex(text=f"VERICHAIN:{doc_sha256}")
        
        tx = {
            'to': account.address,
            'value': 0,
            'gas': 2000000,
            'gasPrice': w3.eth.gas_price,
            'nonce': w3.eth.get_transaction_count(account.address),
            'data': data,
            'chainId': 80002
        }
        
        signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        
        try:
            raw_tx = signed_tx.raw_transaction
        except AttributeError:
            raw_tx = signed_tx.rawTransaction
            
        tx_hash = w3.eth.send_raw_transaction(raw_tx)
        return tx_hash.hex()
    except Exception as e:
        print(f"Blockchain anchoring failed: {e}")
        return None

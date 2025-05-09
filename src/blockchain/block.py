import hashlib
import json
import time
from typing import List, Dict, Any

def hash_pair(a: str, b: str) -> str:
    """
    Calculate combined hash of two hash values.
    
    Args:
        a: First hash string
        b: Second hash string
    
    Returns:
        Combined hash string
    """
    return hashlib.sha256((a + b).encode()).hexdigest()

def compute_merkle_root(tx_hashes: List[str]) -> str:
    """
    Calculate Merkle root hash from transaction hashes.
    
    Args:
        tx_hashes: List of transaction hash strings
    
    Returns:
        Merkle root hash string
    """
    if not tx_hashes:
        return '0' * 64
    if len(tx_hashes) == 1:
        return tx_hashes[0]
    
    new_level = []
    for i in range(0, len(tx_hashes), 2):
        left = tx_hashes[i]
        right = tx_hashes[i+1] if i+1 < len(tx_hashes) else left
        new_level.append(hash_pair(left, right))
    return compute_merkle_root(new_level)

class Block:
    """
    Block class representing a block in the blockchain.
    Contains transactions, timestamp, and cryptographic hashes.
    """
    
    def __init__(self, index: int, transactions: List[Dict[str, Any]], 
                 previous_hash: str, timestamp: float = None, difficulty: int = 2):
        """
        Initialize a new block.
        
        Args:
            index: Block index in the chain
            transactions: List of transaction dictionaries
            previous_hash: Hash of the previous block
            timestamp: Block creation timestamp
            difficulty: Mining difficulty level
        """
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp or time.time()
        self.previous_hash = previous_hash
        self.difficulty = difficulty
        self.nonce = 0
        
        self.merkle_root = self.compute_merkle_root()
        self.hash = self.calculate_hash()

    def compute_merkle_root(self) -> str:
        """Compute Merkle root from transaction hashes"""
        if not self.transactions:
            return "0" * 64  # Empty block hash
            
        tx_hashes = [
            hashlib.sha256(json.dumps(tx, sort_keys=True).encode()).hexdigest()
            for tx in self.transactions
        ]
        return compute_merkle_root(tx_hashes)

    def calculate_hash(self) -> str:
        """Calculate block hash"""
        block_string = json.dumps({
            "index": self.index,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "nonce": self.nonce,
            "merkle_root": self.merkle_root
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def mine_block(self) -> None:
        """
        Mine block by finding nonce that satisfies difficulty requirement.
        Updates block hash and nonce.
        """
        prefix = '0' * self.difficulty
        while not self.hash.startswith(prefix):
            self.nonce += 1
            self.hash = self.calculate_hash()

    def edit_transaction(self, tx_index: int, field: str = None, new_value: Any = None, new_transaction: Dict[str, Any] = None) -> tuple:
        """
        Edit a transaction in the block.
        
        Args:
            tx_index: Index of transaction to edit
            field: Field to modify (optional)
            new_value: New value for the field (optional)
            new_transaction: New transaction to replace (optional)
            
        Returns:
            tuple: (original_transaction, original_merkle_root)
        """
        if tx_index >= len(self.transactions):
            raise IndexError("Transaction index out of range")
            
        # Store original values
        original_tx = self.transactions[tx_index].copy()
        original_merkle = self.merkle_root
        
        # Modify transaction
        if field is not None and new_value is not None:
            self.transactions[tx_index][field] = new_value
        elif new_transaction is not None:
            self.transactions[tx_index] = new_transaction
            
        # Update block hash and merkle root
        self.merkle_root = self.compute_merkle_root()
        self.hash = self.calculate_hash()
        
        return original_tx, original_merkle

    def verify_self(self) -> Dict[str, Any]:
        """
        Verify the internal integrity of this block:
        - Check that merkle_root matches the hash of transactions
        - Check that hash matches the block header (including merkle_root)
        Returns a dict containing:
        - merkle_ok: whether the stored merkle_root is correct
        - hash_ok: whether the stored hash is correct
        - expected_merkle_root: the merkle root recomputed from transactions
        - expected_hash: the hash recomputed from block header
        """
        expected_merkle = self.compute_merkle_root()
        expected_hash   = self.calculate_hash()
        return {
            'merkle_ok': self.merkle_root == expected_merkle,
            'hash_ok':   self.hash == expected_hash,
            'expected_merkle_root': expected_merkle,
            'expected_hash': expected_hash
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert block to dictionary format.
        
        Returns:
            Dictionary containing block data
        """
        return {
            "index": self.index,
            "transactions": self.transactions,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "hash": self.hash,
            "nonce": self.nonce,
            "difficulty": self.difficulty,
            "merkle_root": self.merkle_root
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Block':
        """
        Create block instance from dictionary.
        
        Args:
            data: Dictionary containing block data
            
        Returns:
            Block instance
        """
        block = cls(
            index=data["index"],
            transactions=data["transactions"],
            previous_hash=data["previous_hash"],
            timestamp=data["timestamp"],
            difficulty=data.get("difficulty", 2)
        )
        block.hash = data["hash"]
        block.nonce = data["nonce"]
        block.merkle_root = data.get("merkle_root", '0' * 64)
        return block 
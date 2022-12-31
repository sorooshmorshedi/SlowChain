import json
import hashlib
from time import time
from urllib.parse import urlparse

import requests


class SlowChain(object):
    def __init__(self) -> None:
        self.chain = []
        self.transactions = []
        self.nodes = set()

        self.add_block_to_chain(self.create_block(proof=100, previous_hash=1))

    @property
    def previous_block(self):
        return self.chain[-1]

    def create_block(self, proof, previous_hash=None):
        block = {
            'pk': len(self.chain) + 1,
            'date_time': time(),
            'transactions': self.transactions,
            'proof_of_work': proof,
            'previous_hash': previous_hash or self.to_hash(self.chain[-1])
        }
        return block

    def add_block_to_chain(self, block):
        self.transactions = []
        self.chain.append(block)

    def add_transaction(self, receiver, sender, amount):
        self.transactions.append({
            'to': receiver,
            'from': sender,
            'amount': amount,
        })

        return self.previous_block['pk'] + 1

    def validate_pow(self, first_pow, second_pow):
        proof = str(first_pow) + str(second_pow)
        hash_of_pow = self.sha256(proof)
        return hash_of_pow[:4] == '00'

    def proof_of_work(self, previous_pow):
        proof = 0
        while self.validate_pow(previous_pow, proof):
            proof += 1
        return proof

    def to_hash(self, input):
        input_str = json.dumps(input, sort_keys=True).encode()
        return self.sha256(input_str)

    @staticmethod
    def sha256(sha_input):
        return hashlib.sha256(sha_input).hexdigest()

    def register_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def validate_chain(self, chain):
        previous_block = chain[0]
        current_index = 1
        while current_index < len(chain):
            block = chain[current_index]
            if block['previous_hash'] != self.to_hash(previous_block):
                return False

            if not self.validate_pow(previous_block['proof_of_work'], block['proof_of_work']):
                return False

            previous_block = block
            current_index += 1
        return True

    def resolve_conflicts(self):
        others = self.nodes
        new_chain = None

        max_length = len(self.chain)

        for node in others:
            response = requests.get(f'http://{node}/chain')
            if response.status_code == 200:
                length = response.json()['len_of_chain']
                chain = response.json()['chain']
                if length > max_length and self.validate_chain(chain):
                    max_length = length
                    new_chain = chain
        if new_chain:
            self.chain = new_chain
            return True
        return False

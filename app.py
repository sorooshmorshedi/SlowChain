from urllib import request
from uuid import uuid4
import sys

from flask import Flask, jsonify, request
import requests

from block_chain import SlowChain

app = Flask(__name__)

node_id = str(uuid4())

block_chain = SlowChain()


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    data = request.get_json()
    this_block = block_chain.add_transaction(
        data['recipient'],
        data['sender'],
        data['amount']
    )
    response = {'message': 'transaction add to {}'.format(this_block)}
    return jsonify(response), 201


@app.route("/")
def hello_world():
    return "<p>hello, this is Slow chain!</p>"


@app.route('/blockChain', methods=['GET'])
def block_chain():
    response = {
        'chain':  block_chain.chain,
        'len_of_chain': len(block_chain.chain)
    }
    return jsonify(response), 200


@app.route('/mine', methods=['GET'])
def mine():
    previous_block = block_chain.previous_block
    previous_pow = previous_block['proof_of_work']
    proof = block_chain.proof_of_work(previous_pow)

    block_chain.add_transaction(sender="0", receiver=node_id, amount=12.5)
    previous_hash = block_chain.to_hash(previous_block)
    block = block_chain.create_block(proof, previous_hash)

    response = {
        'message': 'new block created on block chain',
        'pk': block['pk'],
        'transactions': block['transactions'],
        'proof_of_work': block['proof_of_work'],
        'previous_hash': block['previous_hash'],
    }

    return jsonify(response), 200


@app.route('/nodes/register', methods=['POST'])
def register_node():
    values = request.get_json()
    nodes = values.get('nodes')

    for node in nodes:
        block_chain.register_node(node)

    response = {
        'message': 'node registered',
        'nodes': list(block_chain.nodes)
    }
    return jsonify(response), 201


@app.route('node/resolve', methods=['GET'])
def consensus():
    new = block_chain.resolve_conflicts()
    if new:
        response = {
            'message': 'new chain replaced',
            'new_chain': block_chain.chain
        }
    else:
        response = {
            'message': 'my chain replaced',
            'new_chain': block_chain.chain
        }

    return jsonify(response), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=sys.argv[1])


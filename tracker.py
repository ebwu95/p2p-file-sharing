from flask import Flask, request, jsonify
from collections import defaultdict

app = Flask(__name__)

class Tracker:
    def __init__(self):
        self.peers = {}  # stores peers as {peer_id: {"ip": ip, "port": port, "pieces": set()}}
        self.chunk_freq = {} # maps each chunk id to freq

    def register_peer(self, peer_id, ip, port):
        if peer_id not in self.peers:
            self.peers[peer_id] = {"ip": ip, "port": port, "pieces": set()}
        return self.peers[peer_id]

    def update_pieces(self, peer_id, pieces):
        if peer_id in self.peers:
            for piece in pieces:
                if (piece not in self.peers[peer_id]["pieces"]):
                    self.peers[peer_id]["pieces"].add(piece)
                    self.chunk_freq[piece] += 1

    def get_peers(self):
        return self.peers

    def get_peer_info(self, peer_id):
        return self.peers.get(peer_id, None)

    def get_rare_pieces(self):
        rarest_pieces = sorted(chunk_freq.items(), key=lambda x: x[1])
        return [piece for piece, _ in rarest_pieces]

# Initialize the tracker
tracker = Tracker()

@app.route('/register', methods=['POST'])
def register_peer():
    data = request.json
    peer_id = data.get('peer_id')
    ip = request.remote_addr
    port = data.get('port')
    if peer_id and port:
        peer = tracker.register_peer(peer_id, ip, port)
        return jsonify({"message": "Peer registered", "peer": peer}), 201
    return jsonify({"error": "Missing peer_id or port"}), 400

@app.route('/update_pieces', methods=['POST'])
def update_pieces():
    data = request.json
    peer_id = data.get('peer_id')
    pieces = data.get('pieces', [])
    if peer_id and isinstance(pieces, list):
        tracker.update_pieces(peer_id, pieces)
        return jsonify({"message": "Pieces updated"}), 200
    return jsonify({"error": "Missing peer_id or pieces"}), 400

@app.route('/peers', methods=['GET'])
def get_peers():
    return jsonify(tracker.get_peers()), 200

@app.route('/peer/<peer_id>', methods=['GET'])
def get_peer_info(peer_id):
    peer_info = tracker.get_peer_info(peer_id)
    if peer_info:
        return jsonify(peer_info), 200
    return jsonify({"error": "Peer not found"}), 404

@app.route('/rare_pieces', methods=['GET'])
def get_rare_pieces():
    rare_pieces = tracker.get_rare_pieces()
    return jsonify(rare_pieces), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

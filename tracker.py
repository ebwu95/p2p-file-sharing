from flask import Flask, request, jsonify
from collections import defaultdict
import uuid
app = Flask(__name__)


def exclude_self(peers, ip, port):
    return [peers for (peer_ip, peer_port) in peers if (peer_ip, peer_port) != (ip, port)]

# class Torrent:
#     def __init__(self, file_id, ip, port):
#         self.file_id = file_id
#         self.source_ip = ip
#         self.source_port = port 

class Tracker:
    def __init__(self):
        self.nodes = []
        self.torrents = {}
        self.chunk_freq = {} # maps each chunk id to freq

    def register_peer(self, ip, port):
        if (ip, port) not in self.peers:
            peers.append(ip, port)
            return True
        else:
            return False

    def initialize_chunks(self, file_id, file_size, chunk_data):
        self.torrents[file_id] = chunk_data
        self.chunk_freq[file_id] = [0] * file_size
        for ip, port in chunk_data:
            for i, chunk in enumrate(chunk_data[(ip, port)]):
                self.chunk_freq[i] += chunk

    def update_chunks(self, ip, port, file_id, bitfield):
        self.torrents[file_id][(ip, port)] = bitfield

    def get_torrent_info(self, file_id):
        self.torrents[file_id]
        
    def get_peers(self):
        return self.peers
    
    def get_rare_pieces(self, file_id):
        rarest_pieces = sorted(self.chunk_freq[file_id].items(), key=lambda x: x[1])
        return [piece for piece, _ in rarest_pieces]

# Initialize the tracker
tracker = Tracker()

@app.route('/register', methods=['POST'])
def register_peer():
    data = request.json
    ip = request.remote_addr
    port = data.get('port')
    if peer_id and port:
        if (tracker.register_peer(ip, port)):
            return jsonify({"message": "Peer registered"}), 201
        else:
            return jsonify({"message": "Peer already exists"}), 400
    return jsonify({"error": "Missing peer_id or port"}), 400

@app.route('/peers', methods=['GET'])
def get_peers():
    return jsonify({"available_peers", exclude_self(tracker.get_peers(), ip, port)}), 200
    
@app.route('/initialize_chunks', methods=['POST'])
def initialize_chunks():
    data = request.json
    ip = request.remote_addr
    file_id = data.get('file')
    file_size = data.get('file_size')
    port = data.get('port')
    chunk_data = data.get("chunk_data")
    Tracker.initialize_chunks(file_id, chunk_data)
    return jsonify({"message": "Initialized peer chunk data", "chunk_data": tracker.get_torrent_info(torrent)}), 200
    
@app.route('/update_chunks', methods=['POST'])
def update_chunks():
    data = request.json 
    ip = request.remote_addr
    file_id = data.get('file')
    port = data.get('port')
    bitfield = data.get('bitfield')
    Tracker.update_chunks(file_id, (ip, port), bitfield)
    return jsonify({"message": "Updated peer chunk data", "chunk_data": tracker.get_torrent_info(torrent)}), 200

@app.route('/peers', methods=['GET'])
def get_peers():
    return jsonify(tracker.get_peers()), 200

@app.route('/rare_pieces', methods=['GET'])
def get_rare_pieces():
    rare_pieces = tracker.get_rare_pieces()
    return jsonify(rare_pieces), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

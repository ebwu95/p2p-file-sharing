from flask import Flask, request, jsonify
from collections import defaultdict
import random

app = Flask(__name__)


def exclude_self(nodes, node_id):
    return [node for node in nodes if node != node_id]

# class Torrent:
#     def __init__(self, file_id, ip, port):
#         self.file_id = file_id
#         self.source_ip = ip
#         self.source_port = port 
def get_node_id(ip, port):
    return str(ip) + ":" + str(port)

class Tracker:
    def __init__(self):
        self.nodes = []
        self.node_stats = {}
        self.torrents = {}
        self.chunk_freq = {}
        self.chunk_holders = {}
        self.sender = {}

    def register_peer(self, node_id):
        if node_id not in self.nodes:
            self.nodes.append(node_id)
            self.node_stats[node_id] = {
                "uploaded_chunks": 0,
                "downloaded_chunks": 0,
                "uploaded_files": 0,
                "downloaded_files": 0,
                "total_uploaded_bytes": 0,
                "total_downloaded_bytes": 0,
                "successful_connections": 0,
                "failed_connections": 0
            }
            return True
        else:
            return False

    def initialize_chunks(self, file_id, file_size, chunk_data, ip, port):
        self.sender[file_id] = get_node_id(ip, port)
        self.torrents[file_id] = chunk_data
        self.chunk_freq[file_id] = [0 for i in range(file_size)]
        self.chunk_holders[file_id] = [[] for i in range(file_size)] 
        for node_id in chunk_data.keys():
            for i, chunk in enumerate(chunk_data[node_id]):
                if (chunk == 1):
                    self.chunk_holders[file_id][i].append(node_id)
                self.chunk_freq[file_id][i] += chunk
        self.torrents[file_id] = chunk_data

    def update_chunk(self, file_id, node_id, chunk_id):
        try:
            self.torrents[file_id][node_id][chunk_id] = 1
            self.chunk_freq[file_id][chunk_id] += 1
            self.chunk_holders[file_id][chunk_id].append(node_id)
            self.node_stats[node_id]["downloaded_chunks"] += 1
            return True
        except Exception as e:
            return False

    def get_torrent_info(self, file_id):
        return self.torrents[file_id]

    def get_peers(self):
        return self.nodes
    
    def request_chunk(self, node_id, file_id):
        request_id = ""
        rarest_freq = float('inf')
        rarest_chunk = -1
        for chunk_id, freq in enumerate(self.chunk_freq[file_id]):
            if (freq < rarest_freq and self.torrents[file_id][node_id][chunk_id] == 0):
                rarest_freq = freq
                rarest_chunk = chunk_id
                try:
                    request_id = random.choice(self.chunk_holders[file_id][chunk_id])
                except Exception as e:
                    print("Note: exception: ", e)
                    continue 
        if (request_id == "" and rarest_chunk == -1):
            request_id = self.sender[file_id]
        return (rarest_chunk, request_id)
    
    def get_statistics(self):
        return self.node_stats

# Initialize the tracker
tracker = Tracker()

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    ip = request.remote_addr
    port = data.get('port')
    if port:
        if (tracker.register_peer(get_node_id(ip, port))):
            return jsonify({"message": "Peer registered"}), 201
        else:
            return jsonify({"message": "Peer already exists"}), 400
    return jsonify({"error": "Missing port"}), 400

@app.route('/peers', methods=['GET'])
def peers():
    data = request.json
    ip = request.remote_addr
    port = data.get('port')
    return jsonify({"available_peers": exclude_self(tracker.get_peers(), get_node_id(ip, port))}), 200
    
@app.route('/initialize_chunks', methods=['POST'])
def initialize_chunks():
    data = request.json
    ip = request.remote_addr
    port = data.get('port')
    file_id = data.get('file_id')
    file_size = data.get('file_size')
    chunk_data = data.get('chunk_data')
    tracker.initialize_chunks(file_id, file_size, chunk_data, ip, port)
    return jsonify({"message": "Initialized peer chunk data", "torrent_info": tracker.get_torrent_info(file_id)}), 200
    
@app.route('/update_chunk', methods=['POST'])
def update_chunk():
    data = request.json 
    ip = request.remote_addr
    file_id = data.get('file_id')
    port = data.get('port')
    chunk_id = data.get('chunk_id')
    if tracker.update_chunk(file_id, get_node_id(ip, port), chunk_id):
        return jsonify({"message": "Updated peer chunk data", "chunk_data": tracker.get_torrent_info(file_id)}), 200
    else:
        return jsonify({"error": "You need to call /initialize_chunks"}), 400

@app.route('/torrent_data', methods=['GET'])
def torrent_data():
    data = request.json 
    ip = request.remote_addr
    file_id = data.get('file_id')
    return jsonify({"chunk_data": tracker.get_torrent_info(file_id)}), 200

@app.route('/request_chunk', methods=['GET'])
def request_chunk():
    data = request.json
    ip = request.remote_addr
    file_id = data.get('file_id')
    port = data.get('port')
    chunk_id, request_id = tracker.request_chunk(get_node_id(ip, port), file_id)
    return jsonify({"chunk_id": chunk_id, "node": request_id}), 200

@app.route('/stats', methods=['GET'])
def stats():
    return jsonify(tracker.get_statistics()), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
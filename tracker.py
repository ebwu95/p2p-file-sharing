from flask import Flask, request, jsonify
from collections import defaultdict

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
        self.torrents = {}
        self.chunk_freq = {} # maps each chunk id to freq
        self.chunk_holders = {}

    def register_peer(self, node_id):
        if node_id not in self.nodes:
            self.nodes.append(node_id)
            return True
        else:
            return False

    def initialize_chunks(self, file_id, file_size, chunk_data):
        self.torrents[file_id] = chunk_data
        self.chunk_freq[file_id] = [0] * file_size
        self.chunk_holders[file_id] = [[]] * file_size
        for node_id in chunk_data.keys():
            for i, chunk in enumerate(chunk_data[node_id]):
                self.chunk_holders[file_id][i].append(node_id)
                self.chunk_freq[file_id][i] += chunk
        self.torrents[file_id] = chunk_data

    def update_chunk(self, node_id, file_id, chunk_id):    
        try:
            self.torrents[file_id][node_id][chunk_id] = 1
            self.chunk_freq[file_id][chunk_id] += 1
            self.chunk_holders[file_id][chunk_id].append(node_id)
            return True
        except Exception as e:
            return False

    def get_torrent_info(self, file_id):
        return self.torrents[file_id]

    def get_peers(self):
        return self.nodes
    
    def get_rarest_holder(self, node_id, file_id):
        request_ip = -1
        request_port = -1
        rarest_freq = float('inf')
        rarest_chunk = -1
        for chunk_id, chunk in enumerate(chunk_freq[file_id]):
            if (chunk_freq[file_id][chunk_id] < rarest_freq and torrents[file_id][node_id][chunk_id] == 0):
                rarest_freq = chunk_freq[file_id][chunk_id] 
                request_ip, request_port = random.choice(chunk_holders[file_id][chunk_id])
                rarest_chunk = chunk_id
        rarest_pieces = sorted(self.chunk_freq[file_id].items(), key=lambda x: x[1])
        return (rarest_chunk, get_node_id(request_ip, request_port))

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
    file_id = data.get('file_id')
    file_size = data.get('file_size')
    chunk_data = data.get('chunk_data')
    tracker.initialize_chunks(file_id, file_size, chunk_data)
    return jsonify({"message": "Initialized peer chunk data", "torrent_info": tracker.get_torrent_info(file_id)}), 200
    
@app.route('/update_chunk', methods=['POST'])
def update_chunk():
    data = request.json 
    ip = request.remote_addr
    file_id = data.get('file_id')
    port = data.get('port')
    chunk_id = data.get('chunk_id')
    tracker.update_chunk(file_id, get_node_id(ip, port), chunk_id)
    return jsonify({"message": "Updated peer chunk data", "chunk_data": tracker.get_torrent_info(torrent)}), 200

@app.route('/peers', methods=['GET'])
def get_peers():
    return jsonify(tracker.get_peers()), 200

@app.route('/request_chunk', methods=['GET'])
def request_chunk():
    data = request.json
    ip = request.remote_addr
    file_id = data.get('file_id')
    port = data.get('port')
    chunk_id, request_ip, request_port = tracker.request_chunk(ip, port, file_id)
    return jsonify({"chunk_id": chunk_id, "ip": request_ip, "port":request_port}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6969)

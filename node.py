import socket
import threading
import os
import traceback
import time
import requests
from file_utils import chunk_file, reassemble_file, compute_sha256

CHUNK_SIZE = 512  # Size of each chunk
BASEURL = "http://localhost:8080"

class Node:
    def __init__(self, port):
        self.port = port
        self.chunks = []  # To hold the actual chunks
        self.bitfield = []  # To track available chunks
        self.server_thread = threading.Thread(target=self.start_server)
        self.server_thread.daemon = True  # Daemonize thread to end with main program
        self.server_thread.start()

    def start_server(self):
        """Starts a peer server that listens for incoming connections."""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(('0.0.0.0', self.port))
        server_socket.listen(5)
        
        url = BASEURL + "/register" 
        data = {"port": self.port}

        try:
            response = requests.post(url, json=data)
            response.raise_for_status()
            print(f"Node registered successfully with port {self.port}")
        except requests.exceptions.RequestException as e:
            print(f"Error registering node: {e}")

        print(f"Peer listening on port {self.port}...")

        while True:
            conn, addr = server_socket.accept()
            print(f"Connected by {addr}")
            threading.Thread(target=self.handle_incoming_client, args=(conn,)).start()

    def handle_incoming_client(self, conn):
        """Handles messages from incoming connections."""
        try:
            # Receive file name
            file_name = self.receive_data(conn)
            print(f"Receiving file: {file_name}")

            # Receive the number of chunks
            num_chunks_data = self.receive_data(conn)
            print(f"Received num_chunks_data: {num_chunks_data}")

            if not num_chunks_data:
                print("Received empty data for number of chunks. Possible end of transmission.")
                return

            try:
                num_chunks = int(num_chunks_data)
                print(f"Expecting {num_chunks} chunks.")
            except ValueError:
                print(f"Received invalid number of chunks: {num_chunks_data}")
                if num_chunks_data == compute_sha256(file_name):  # Check if it's the file hash
                    print("Received file hash. File transfer completed.")
                    return
                raise

            # Initialize the local bitfield
            self.bitfield = [0] * num_chunks
            self.chunks = [None] * num_chunks

            # Send acknowledgment for setup
            self.send_data(conn, "READY")

            # Receive and process chunks
            for _ in range(num_chunks):
                chunk_index_bytes = conn.recv(4)
                chunk_index = int.from_bytes(chunk_index_bytes, byteorder='big')
                chunk_size_bytes = conn.recv(4)
                chunk_size = int.from_bytes(chunk_size_bytes, byteorder='big')
                
                chunk_data = b''
                while len(chunk_data) < chunk_size:
                    packet = conn.recv(min(4096, chunk_size - len(chunk_data)))
                    if not packet:
                        raise Exception("Connection closed while receiving chunk data")
                    chunk_data += packet

                print(f"Received chunk {chunk_index} (size: {chunk_size} bytes)")
                self.chunks[chunk_index] = chunk_data
                self.bitfield[chunk_index] = 1
                self.send_data(conn, "ACK")

            # Receive the original hash to verify integrity
            original_hash = self.receive_data(conn)
            print(f"Received file hash: {original_hash}")

            # Reassemble file
            output_path = os.path.join('received_files', file_name)
            reassemble_file(self.chunks, output_path, original_hash)
            print(f"File {file_name} received and reassembled successfully.")

        except Exception as e:
            print(f"Error while handling incoming client: {e}")
            print(traceback.format_exc())
        finally:
            conn.close()

    def upload(self, file):
        """Connects to multiple peers to upload a file in chunks."""
        print(f"Starting upload process for file: {file}")
        url = BASEURL + "/peers" 
        data = {"port": self.port}

        try:
            response = requests.get(url, json=data)
            data = response.json()
            nodes = data["available_peers"]
            
            response.raise_for_status()
            print(f"Node registered successfully with port {self.port}")
            print(f"Available peers: {nodes}")
        except requests.exceptions.RequestException as e:
            print(f"Error registering node: {e}")
            return

        # Chunk the file and store chunks
        print(f"Chunking file: {file}")
        chunks = chunk_file(file)
        self.chunks = chunks
        num_chunks = len(chunks)
        print(f"File chunked into {num_chunks} chunks")

        # Prepare peers for round-robin sending
        peer_count = len(nodes)
        if peer_count == 0:
            print("No peers available for sending.")
            return

        # Create connections to all peers
        peer_connections = []
        for node in nodes:
            ip, port = node.split(':')
            try:
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.connect((ip, int(port)))
                peer_connections.append(client_socket)
                print(f"Connected to peer {ip}:{port}")

                # Send the file name and number of chunks
                file_name = os.path.basename(file)
                self.send_data(client_socket, file_name)
                self.send_data(client_socket, str(num_chunks))
                print(f"Sent file name '{file_name}' and chunk count {num_chunks} to peer {ip}:{port}")

                # Wait for receiver to be ready
                ready_signal = self.receive_data(client_socket)
                if ready_signal != "READY":
                    raise Exception(f"Receiver not ready. Received: {ready_signal}")
                print(f"Received READY signal from peer {ip}:{port}")

            except Exception as e:
                print(f"Failed to connect to peer {ip}:{port}: {e}")
                if client_socket:
                    client_socket.close()

        if not peer_connections:
            print("No peers available after connection attempts.")
            return

        print(f"Successfully connected to {len(peer_connections)} peers")

        # Distribute chunks among connected peers
        for i, chunk in enumerate(chunks):
            peer_index = i % len(peer_connections)
            client_socket = peer_connections[peer_index]

            try:
                # Send the chunk index and chunk size
                chunk_index_bytes = i.to_bytes(4, byteorder='big')
                chunk_size_bytes = len(chunk).to_bytes(4, byteorder='big')
                
                client_socket.sendall(chunk_index_bytes)
                client_socket.sendall(chunk_size_bytes)
                client_socket.sendall(chunk)

                print(f"Sent chunk {i}/{num_chunks} (size: {len(chunk)} bytes) to peer {peer_index}")

                # Wait for acknowledgment
                ack = self.receive_data(client_socket)
                if ack != "ACK":
                    print(f"Chunk {i} not acknowledged by peer {peer_index}: {ack}")
                else:
                    print(f"Received ACK for chunk {i} from peer {peer_index}")

            except Exception as e:
                print(f"An error occurred while sending chunk {i} to peer {peer_index}: {e}")
                print(f"Traceback: {traceback.format_exc()}")
                # If a peer disconnects, remove it from the list and continue with remaining peers
                peer_connections.pop(peer_index)
                if not peer_connections:
                    print("All peers disconnected. Upload failed.")
                    return

        print("All chunks sent successfully")

        # Send the original file hash after all chunks have been sent
        original_hash = compute_sha256(file)
        for index, client_socket in enumerate(peer_connections):
            try:
                self.send_data(client_socket, original_hash)
                print(f"Sent original file hash to peer {index}.")
            except Exception as e:
                print(f"Failed to send hash to peer {index}: {e}")

        # Close all connections
        for client_socket in peer_connections:
            client_socket.close()

        print(f"File {file_name} upload completed.")

    def send_data(self, sock, data):
        """Send data prefixed with its length."""
        data = data.encode() if isinstance(data, str) else data
        length = len(data).to_bytes(4, byteorder='big')
        sock.sendall(length + data)

    def receive_data(self, sock):
        """Receive data prefixed with its length."""
        length_bytes = sock.recv(4)
        if not length_bytes:
            return None
        length = int.from_bytes(length_bytes, byteorder='big')
        data = b''
        while len(data) < length:
            chunk = sock.recv(min(4096, length - len(data)))
            if not chunk:
                raise Exception("Connection closed while receiving data")
            data += chunk
        return data.decode()

    def run(self):
        """Continues allowing peer to initiate outgoing connections."""
        while True:
            action = input("Do you want to upload a file to another peer? (y/n): ").lower()
            if action == 'y':
                file_path = input("Enter the file path to upload: ")
                self.upload(file_path)
            else:
                print("Waiting for incoming connections...")
                time.sleep(1)  # Add a small delay to prevent busy-waiting

# Ensure the program runs by adding the proper entry point below.
if __name__ == "__main__":
    peer_port = int(input("Enter the port for this peer: "))

    # Ensure 'received_files' directory exists to store downloaded files
    if not os.path.exists('received_files'):
        os.makedirs('received_files')

    peer_instance = Node(peer_port)
    peer_instance.run()
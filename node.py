import socket
import threading
import os
import traceback
import time
import requests
from file_utils import chunk_file, reassemble_file, compute_sha256

CHUNK_SIZE = 512  # Size of each chunk
BASEURL = "http://localhost:8080"

class ChunkSender(threading.Thread):
    def __init__(self, ip, port, chunks, total_chunks, file_name):
        super().__init__()
        self.ip = ip
        self.port = port
        self.chunks = chunks
        self.total_chunks = total_chunks
        self.file_name = file_name

    def run(self):
        """Connects to a peer and sends assigned chunks."""
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((self.ip, self.port))
            print(f"Connected to peer {self.ip}:{self.port}")
            client_socket.sendall(self.file_name.encode())
            time.sleep(0.2)

            # Send the number of chunks assigned to this peer
            num_chunks = len(self.chunks)
            chunk_info = str(num_chunks) + "/" + str(self.total_chunks)
            client_socket.sendall(str(chunk_info).encode())

            # Wait for receiver to be ready
            ready_signal = client_socket.recv(1024).decode()
            if ready_signal != "READY":
                raise Exception("Receiver not ready")

            # Send chunks
            for i, chunk in self.chunks:
                chunk_index_bytes = i.to_bytes(4, byteorder='big')
                chunk_size_bytes = len(chunk).to_bytes(4, byteorder='big')
                
                client_socket.sendall(chunk_index_bytes)
                client_socket.sendall(chunk_size_bytes)
                client_socket.sendall(chunk)
                
                print(f"Sent chunk {i} (size: {len(chunk)} bytes)")
                
                ack = client_socket.recv(1024).decode()
                if ack != "ACK":
                    print(f"Chunk {i} not acknowledged by peer: {ack}")
                    break

                # self.uploaded_chunks += 1
                # self.total_uploaded_bytes += len(chunk)

            print(f"File {self.file_name} sent successfully.")
            # self.uploaded_files += 1
        except Exception as e:
            print(f"Error sending chunks to {self.ip}:{self.port}: {e}")
            print(traceback.format_exc())
        finally:
            client_socket.close()

class Node:
    def __init__(self, port):
        self.port = port
        self.chunks = []  # To hold the actual chunks
        self.bitfield = []  # To track available chunks
        self.server_thread = threading.Thread(target=self.start_server)
        self.server_thread.daemon = True  # Daemonize thread to end with main program
        self.server_thread.start()
        self.uploaded_chunks = 0
        self.downloaded_chunks = 0
        self.uploaded_files = 0
        self.downloaded_files = 0
        self.total_uploaded_bytes = 0
        self.total_downloaded_bytes = 0
        self.successful_connections = 0
        self.failed_connections = 0

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
            message = conn.recv(1024).decode().strip()
            if (message.startswith("GET_CHUNK")):
                request_type, file, chunk_id = message.split(":")
                chunk_id = int(chunk_id)
                chunk = self.chunks[chunk_id]
                chunk_size_bytes = len(chunk).to_bytes(4, byteorder='big')
                conn.sendall(chunk_size_bytes)
                conn.sendall(chunk)
            elif (message.startswith("QDOWNLOAD")):
                _, file_name, total, original_hash = message.split(":")
                print("ASKING QDOWNLOAD NOW")
                total_chunks = int(total)
                while (self.downloaded_chunks < total_chunks):
                    self.download_chunk(file_name)
                new_file = file_name + str(self.port)
                output_path = os.path.join('received_files', new_file)
                reassemble_file(self.chunks, output_path, original_hash)
                print(f"File {file_name} retrieved and reassambled successfully.")
            else:
                file_name = message
                print(f"Receiving file: {file_name}")

                # Receive the number of chunks
                num_chunks, total_chunks = conn.recv(1024).decode().split("/")
                num_chunks = int(num_chunks)
                total_chunks = int(total_chunks)
                print(f"Expecting {num_chunks} chunks.")

                # Initialize the local bitfield
                self.bitfield = [0] * total_chunks
                self.chunks = [None] * total_chunks

                # Send acknowledgment for setup
                conn.sendall("READY".encode())

                # Receive and process chunks
                for i in range(num_chunks):
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
                    print(f"Adding chunk {chunk_index} with value {chunk_data} to chunks")
                    self.chunks[chunk_index] = chunk_data
                    self.bitfield[chunk_index] = 1
                    conn.sendall("ACK".encode())

                    # Update statistics
                    self.downloaded_chunks += 1
                    self.total_downloaded_bytes += chunk_size

                # Receive the original hash to verify integrity
                self.downloaded_files += 1

        except Exception as e:
            print(f"Error while handling incoming client: {e}")
            print(traceback.format_exc())
            self.failed_connections += 1
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
        num_peers = len(nodes)
        if num_peers == 0:
            print("No peers available for sending.")
            return

        chunk_block_sz = num_chunks // num_peers
        # Create a connection for each peer and keep it open
        threads = []
        chunk_data = {}
        for i, peer in enumerate(nodes):
            peer_ip, peer_port = peer.split(":")
            chunk_data[peer] = [0 for j in range(num_chunks)]
            for j in range(i * chunk_block_sz, min(num_chunks, ((i+1) * chunk_block_sz))):
                chunk_data[peer][j] = 1
            assigned_chunks = [(j, chunks[j]) for j in range(i * chunk_block_sz, min(num_chunks, ((i+1) * chunk_block_sz)))]
            thread = ChunkSender(peer_ip, int(peer_port), assigned_chunks, num_chunks, file)
            thread.start()
            threads.append(thread)

        # Wait for all threads to finish
        for thread in threads:
            thread.join()
        print("all chunks sent successfully")
        
        print("chunk_data", chunk_data)
        url = BASEURL + "/initialize_chunks" 
        data = {"file_id": file,  "file_size": num_chunks, "chunk_data": chunk_data}
        try:
            response = requests.post(url, json=data)
            response.raise_for_status()
            print(f"Torrent initialized")
            print(f"Available peers: {nodes}")
        except requests.exceptions.RequestException as e:
            print(f"Error registering node: {e}")
            return
        
        original_hash = compute_sha256(file)

        for node in nodes:
            ip, port = node.split(":")
            try:
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.connect((ip, int(port)))
                message = "QDOWNLOAD:" + file + ":" + str(num_chunks) + ":" + original_hash
                client_socket.sendall(message.encode()) # let the nodes know everybody is ready
            except Exception as e:
                print("ERROR SENDING MESSAGE: ", e)
                return 
            finally:
                client_socket.close()
        print(f"File {file} upload completed.")

    def get_statistics(self):
        """Return network statistics as a dictionary"""
        return {
            "uploaded_chunks": self.uploaded_chunks,
            "downloaded_chunks": self.downloaded_chunks,
            "uploaded_files": self.uploaded_files,
            "downloaded_files": self.downloaded_files,
            "total_uploaded_bytes": self.total_uploaded_bytes,
            "total_downloaded_bytes": self.total_downloaded_bytes,
            "successful_connections": self.successful_connections,
            "failed_connections": self.failed_connections
        }
        
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

    def runViaButton(self, file_path):
        """Continues allowing peer to initiate outgoing connections."""
        self.upload(file_path)
        time.sleep(1)  # Add a small delay to prevent busy-waiting

    def download_chunk(self, file_name):
        # Request chunk information from tracker
        tracker_url = BASEURL+'/request_chunk'

        data = {
            "file_id": file_name,
            "port": self.port
        }

        try:
            # Request data for that chunk from the tracker
            response = requests.get(tracker_url, json=data)
            print(f"Tracker response for chunk : {response.json()}")
            data = response.json()

            chunk_id = data["chunk_id"]
            target_node = data["node"]

            # Extract IP and port from target_node
            target_ip, target_port = target_node.split(':')
            target_port = int(target_port)

            # Establish connection with the target node
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((target_ip, target_port))

                # Send request for the specific chunk
                request = f"GET_CHUNK:{file_name}:{chunk_id}"
                s.sendall(request.encode())

                # Receive chunk size
                chunk_size_bytes = s.recv(4)
                chunk_size = int.from_bytes(chunk_size_bytes, byteorder='big')

                # Receive chunk data
                chunk_data = b''
                while len(chunk_data) < chunk_size:
                    packet = s.recv(min(4096, chunk_size - len(chunk_data)))
                    if not packet:
                        raise Exception("Connection closed while receiving chunk data")
                    chunk_data += packet
                self.chunks[chunk_id] = chunk_data
                # idk if we need to return it, maybe just append to self_chunklist, then send updated bitmap to tracker.
                # HOw do we assemble at end? maybe send an arbitrary command to the downloader to check if they have a full bitmap/ some other condition?
            tracker_url = BASEURL+'/update_chunk'
            data = {
                "file_id": file_name,
                "port": self.port,
                "chunk_id": chunk_id
            }
            response = requests.post(tracker_url, json=data)
            print(f"Successfully downloaded chunk {chunk_id} (size: {len(chunk_data)} bytes)")
            self.downloaded_chunks += 1
        except Exception as e:
            print("ERROR: ", e)

# Ensure the program runs by adding the proper entry point below.
if __name__ == "__main__":
    peer_port = int(input("Enter the port for this peer: "))

    # Ensure 'received_files' directory exists to store downloaded files
    if not os.path.exists('received_files'):
        os.makedirs('received_files')

    peer_instance = Node(peer_port)
    peer_instance.run()

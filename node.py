import socket
import threading
import os
from file_utils import chunk_file, reassemble_file, save_chunks, compute_sha256

class Node:
    def __init__(self, port):
        self.port = port
        self.server_thread = threading.Thread(target=self.start_server)
        self.server_thread.daemon = True  # Daemonize thread to end with main program
        self.server_thread.start()

    def start_server(self):
        """Starts a peer server that listens for incoming connections."""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(('0.0.0.0', self.port))  # Bind to all network interfaces
        server_socket.listen(5)  # Listen for up to 5 connections
        print(f"Peer listening on port {self.port}...")

        while True:
            conn, addr = server_socket.accept()  # Accept new connections
            print(f"Connected by {addr}")
            threading.Thread(target=self.handle_incoming_client, args=(conn,)).start()

    def handle_incoming_client(self, conn):
        """Handles messages from incoming connections."""
        file_name = conn.recv(1024).decode()  
        print(f"Receiving file: {file_name}")
        
        original_hash = conn.recv(64).decode()  # Receive the original hash
        print(f"Original hash: {original_hash}")

        chunks = []
        while True:
            # Receive file chunks
            data = conn.recv(512)  # 512-byte chunks as defined
            if not data:
                break
            chunks.append(data)
        
        # Reassemble file
        output_path = os.path.join('received_files', file_name)  # Store in a folder
        reassemble_file(chunks, output_path, original_hash)  # Pass the original hash

    def send_file(self, ip, port, file_path):
        """Sends a file to a peer."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((ip, port))
            file_name = os.path.basename(file_path)
            s.sendall(file_name.encode())

            original_hash = compute_sha256(file_path)  # Compute the original hash
            s.sendall(original_hash.encode())  # Send the original hash

            chunks = chunk_file(file_path)
            for chunk in chunks:
                s.sendall(chunk)
            print(f"File {file_name} sent successfully.")

if __name__ == "__main__":
    peer_port = int(input("Enter the port for this peer: "))
    
    # Ensure 'received_files' directory exists to store downloaded files
    if not os.path.exists('received_files'):
        os.makedirs('received_files')
    
    peer_instance = Node(peer_port)
    peer_instance.run()
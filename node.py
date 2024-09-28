import socket
import threading
import os
from file_utils import chunk_file, reassemble_file, save_chunks

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
        
        chunks = []
        while True:
            # Receive file chunks
            data = conn.recv(512)  # 512-byte chunks as defined
            if not data:
                break
            chunks.append(data)
        # Reassemble file
        output_path = os.path.join('received_files', file_name)  # Store in a folder
        reassemble_file(chunks, output_path)
        print(f"File {file_name} received and reassembled successfully.")

    def connect_to_peer(self, ip, port, file):
        """Connects to another peer to upload a file."""
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client_socket.connect((ip, port))  # Connect to another peer
            print(f"Connected to peer {ip}:{port}")

            # Send the file name
            file_name = os.path.basename(file)
            client_socket.sendall(file_name.encode())  
            
            # Chunk and send the file
            chunks = chunk_file(file)
            for chunk in chunks:
                client_socket.sendall(chunk)
                
            print(f"File {file_name} sent successfully.")
        
        except socket.error as e:
            print(f"Connection error: Could not connect to peer at {ip}:{port} - {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        finally:
            client_socket.close()

    def run(self):
        """Continues allowing peer to initiate outgoing connections."""
        while True:
            action = input("Do you want to upload a file to another peer? (y/n): ").lower()
            if action == 'y':
                target_ip = input("Enter the IP address of the peer to connect to: ")
                target_port = int(input("Enter the port of the peer to connect to: "))
                file_path = input("Enter the file path to upload: ")
                self.connect_to_peer(target_ip, target_port, file_path)
            else:
                print("Waiting for incoming connections...")

if __name__ == "__main__":
    peer_port = int(input("Enter the port for this peer: "))
    
    # Ensure 'received_files' directory exists to store downloaded files
    if not os.path.exists('received_files'):
        os.makedirs('received_files')
    
    peer_instance = Node(peer_port)
    peer_instance.run()
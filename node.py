import socket
import threading
import os
from file_utils import chunk_file, reassemble_file

CHUNK_SIZE = 512  # Size of each chunk

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
        server_socket.bind(('0.0.0.0', self.port))  # Bind to all network interfaces
        server_socket.listen(5)  # Listen for up to 5 connections
        print(f"Peer listening on port {self.port}...")

        while True:
            conn, addr = server_socket.accept()  # Accept new connections
            print(f"Connected by {addr}")
            threading.Thread(target=self.handle_incoming_client, args=(conn,)).start()

    def handle_incoming_client(self, conn):
        """Handles messages from incoming connections."""
        try:
            # Receive file name
            file_name = conn.recv(1024).decode()
            print(f"Receiving file: {file_name}")

            # Receive the bitfield
            bitfield_data = conn.recv(1024)  # Assume bitfield is sent right after filename
            peer_bitfield = list(bitfield_data)

            # Initialize the local bitfield to match the peer's bitfield
            self.bitfield = [0] * len(peer_bitfield)  # Ensure it's the same size
            print(f"Received bitfield: {peer_bitfield}")

            # Request missing chunks from the peer
            self.request_missing_chunks(peer_bitfield, conn)

            # Receive the chunks
            chunks = []
            while True:
                data = conn.recv(CHUNK_SIZE)
                if not data:
                    break
                chunks.append(data)

            # Reassemble file
            output_path = os.path.join('received_files', file_name)  # Store in a folder
            reassemble_file(chunks, output_path)
            print(f"File {file_name} received and reassembled successfully.")

        except Exception as e:
            print(f"Error while handling incoming client: {e}")
        finally:
            conn.close()

    def request_missing_chunks(self, peer_bitfield, conn):
        """Requests missing chunks from a peer's bitfield."""
        for i, has_chunk in enumerate(peer_bitfield):
            # Make sure we only request from the peer if they have the chunk
            if has_chunk and (i >= len(self.bitfield) or not self.bitfield[i]):
                print(f"Requesting missing chunk {i} from peer.")
                conn.sendall(f"request_chunk:{i}".encode())  # Request the specific chunk
                response = conn.recv(CHUNK_SIZE)
                if response:
                    self.chunks.append(response)  # Append received chunk to our list
                    self.bitfield[i] = 1  # Mark chunk as received

    def handle_chunk_request(self, conn, chunk_index):
        """Handles requests for chunks from peers."""
        if chunk_index < len(self.chunks):
            print(f"Sending chunk {chunk_index} to peer.")
            conn.sendall(self.chunks[chunk_index])  # Send the requested chunk
        else:
            print(f"Chunk {chunk_index} not available.")

    def connect_to_peer(self, ip, port, file):
        """Connects to another peer to upload a file."""
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client_socket.connect((ip, port))  # Connect to another peer
            print(f"Connected to peer {ip}:{port}")

            # Send the file name
            file_name = os.path.basename(file)
            client_socket.sendall(file_name.encode())

            # Chunk the file and store chunks
            chunks = chunk_file(file)
            self.chunks = chunks  # Store the chunks
            self.bitfield = [1] * len(chunks)  # All chunks are available

            # Send the bitfield to the peer
            client_socket.sendall(bytearray(self.bitfield))

            # Send the chunks
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
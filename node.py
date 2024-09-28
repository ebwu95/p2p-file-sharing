import socket
import threading
import os
from file_utils import chunk_file, reassemble_file, save_chunks, compute_sha256

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

        while True:
            conn, addr = server_socket.accept()  # Accept new connections
            threading.Thread(target=self.handle_incoming_client, args=(conn,)).start()

    # This method is called to receive client info after they do sendall
    # RECEIVE BITFIELD HERE
    def handle_incoming_client(self, conn):
        """Handles messages from incoming connections."""
        try:
            # Receive file name and hash
            data = conn.recv(1024).decode()
            print("THIS S THE RECEIVED DATA: ",data)
            file_name, original_hash = data.split('|')

            # Next, Receive the bitfield
            bitfield_data = conn.recv(1024)
            peer_bitfield = list(bitfield_data)

            print("Received bitfield from peer:", peer_bitfield)
            print("End of bitfield")

            # Initialize the local bitfield to match the peer's bitfield
            if len(self.bitfield)==0 :   
                self.bitfield = [0] * len(peer_bitfield)

            # Request missing chunks from the peer
            self.request_missing_chunks(peer_bitfield, conn)

            # Now, Receive the chunks from the request

            while True:
                # Receiving requests from the peer
                data = conn.recv(1024)
                if not data:
                    break  # Exit if no data is received
                            # Check if the request is for a chunk
                if data.startswith("request_chunk:"):
                    chunk_index = int(data.split(":")[1])
                    print(f"Peer requested chunk {chunk_index}")
                    self.handle_chunk_request(conn, chunk_index)



            # chunks = []
            # while True:
            #     data = conn.recv(CHUNK_SIZE)
            #     if not data:
            #         break
            #     chunks.append(data)

            # Reassemble file
            output_path = os.path.join('received_files', file_name)  # Store in a folder

            #BAD, only reassemble once chunks is all full
            #reassemble_file(chunks, output_path, original_hash)

        except Exception as e:
            pass  # Handle errors silently as per your request
        finally:
            conn.close()

    # Selection Method?
    def request_missing_chunks(self, peer_bitfield, conn):
        print("Starting to request missing chunks...")

        for i, has_chunk in enumerate(peer_bitfield):
            if has_chunk and (i >= len(self.bitfield) or not self.bitfield[i]):
                print(f"Requesting chunk {i} from peer...")
                conn.sendall(f"request_chunk:{i}".encode())

                # Request sent, now listening to receive the chunk
                try:
                    response = conn.recv(CHUNK_SIZE)
                    if response:
                        print(f"Received chunk {i} from peer.")
                        self.chunks.append(response) # append the chunk to its chunk list
                        self.bitfield[i] = 1  # Mark chunk as received
                    else:
                        print(f"Did not receive chunk {i}, received empty data.")
                except socket.error as e:
                    print(f"Error receiving chunk {i}: {e}")
                    break  # Exit the loop if there's an issue  

        print ("After requesting this is MY bitfield: ",self.bitfield)

    def handle_chunk_request(self, conn, chunk_index):
        """Handles requests for chunks from peers."""
        if chunk_index < len(self.chunks):
            conn.sendall(self.chunks[chunk_index])  # Send the requested chunk

    def send_file(self, ip, port, file_path):
        """Sends a file to a peer."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((ip, port))
            file_name = os.path.basename(file_path)
            original_hash = compute_sha256(file_path)
            header = f"{file_name}|{original_hash}"
            s.sendall(header.encode())

            # Chunk the file and store chunks
            chunks = chunk_file(file_path)
            self.chunks = chunks  # Store the chunks
            self.bitfield = [1] * len(chunks)  # All chunks are available

            # Send the bitfield to the peer
            s.sendall(bytearray(self.bitfield))

            print("Sent bittfield!")
            
            # # Send the chunks
            # for chunk in chunks:
            #     s.sendall(chunk)

    def run(self):
        """Continues allowing peer to initiate outgoing connections."""
        while True:
            action = input("Do you want to upload a file to another peer? (y/n): ").lower()
            if action == 'y':
                target_ip = input("Enter the IP address of the peer to connect to: ")
                target_port = int(input("Enter the port of the peer to connect to: "))
                file_path = input("Enter the file path to upload: ")
                self.send_file(target_ip, target_port, file_path)

if __name__ == "__main__":
    peer_port = int(input("Enter the port for this peer: "))

    # Ensure 'received_files' directory exists to store downloaded files
    if not os.path.exists('received_files'):
        os.makedirs('received_files')

    peer_instance = Node(peer_port)
    peer_instance.run()

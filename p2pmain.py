import socket
import threading

# --- Peer as Server (Listener) ---
def start_peer_server(port):
    """Starts a peer server that listens for incoming connections."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', port))  # Bind to all network interfaces
    server_socket.listen(5)  # Listen for up to 5 connections
    print(f"Peer listening on port {port}...")

    while True:
        conn, addr = server_socket.accept()  # Accept new connections
        print(f"Connected by {addr}")
        threading.Thread(target=handle_incoming_client, args=(conn,)).start()

def handle_incoming_client(conn):
    """Handles messages from incoming connections."""
    data = conn.recv(1024)  # Receive data
    print(f"Received: {data.decode()}")
    
    # Send a response
    conn.sendall(b'Hello from peer!')
    conn.close()

# --- Peer as Client (Connector) ---
def connect_to_peer(ip, port):
    """Connects to another peer and sends a message."""
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        client_socket.connect((ip, port))  # Connect to another peer
        print(f"Connected to peer {ip}:{port}")
        
        # Send a message
        client_socket.sendall(b'Hello, peer!')
        
        # Receive a response
        response = client_socket.recv(1024)
        print(f"Received from peer: {response.decode()}")
    
    except socket.error as e:
        print(f"Connection error: Could not connect to peer at {ip}:{port} - {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        client_socket.close()

# --- Main Peer Function ---
def peer(port):
    """Starts a peer that can listen and connect."""
    
    # Start server in a new thread to listen for incoming connections
    server_thread = threading.Thread(target=start_peer_server, args=(port,))
    server_thread.daemon = True  # Daemonize thread to end with main program
    server_thread.start()
    
    # Continue allowing peer to initiate outgoing connections
    while True:
        action = input("Do you want to connect to another peer? (y/n): ").lower()
        if action == 'y':
            target_ip = input("Enter the IP address of the peer to connect to: ")
            target_port = int(input("Enter the port of the peer to connect to: "))
            connect_to_peer(target_ip, target_port)
        else:
            print("Waiting for incoming connections...")

if __name__ == "__main__":
    peer_port = int(input("Enter the port for this peer: "))
    peer(peer_port)


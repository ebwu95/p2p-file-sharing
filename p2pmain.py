import socket
import threading

# --- Server Code ---
def start_server(port):
    """Starts a TCP server that listens for incoming connections."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', port))  # Bind to all network interfaces
    server_socket.listen(5)  # Listen for up to 5 connections
    print(f"Server listening on port {port}...")

    while True:
        conn, addr = server_socket.accept()  # Accept new connections
        print(f"Connected by {addr}")
        threading.Thread(target=handle_client, args=(conn,)).start()

def handle_client(conn):
    """Handles incoming message from the client."""
    data = conn.recv(1024)  # Receive data from client
    print(f"Received: {data.decode()}")
    
    # Send a response back to the client
    conn.sendall(b'Hello, client!')
    conn.close()

# --- Client Code ---
def connect_to_server(ip, port):
    """Connects to the server and sends a message."""
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((ip, port))  # Connect to the server
    print(f"Connected to server {ip}:{port}")
    
    # Send a test message
    client_socket.sendall(b'Hello, server!')
    
    # Receive response from the server
    response = client_socket.recv(1024)
    print(f"Received from server: {response.decode()}")
    
    # Close the connection
    client_socket.close()

# --- Main Section ---
if __name__ == "__main__":
    choice = input("Do you want to start the server or client? (s/c): ").lower()

    if choice == 's':
        # Start the server on port 5000
        start_server(5000)
    elif choice == 'c':
        # Connect to the server (localhost on port 5000)
        connect_to_server('127.0.0.1', 5000)
    else:
        print("Invalid choice. Please select 's' for server or 'c' for client.")

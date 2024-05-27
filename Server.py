import socket
import threading
import pyaudio
import ssl
from concurrent.futures import ThreadPoolExecutor

# Server configuration
HOST = '10.1.20.242'  # Listen on all available interfaces
PORT = 12345

# PyAudio configuration
CHUNK_SIZE = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

# SSL configuration
CERT_FILE = r"C:\Users\vijju\OneDrive\Desktop\Sem-4\CN\VOIP\server.crt"
KEY_FILE = r"C:\Users\vijju\OneDrive\Desktop\Sem-4\CN\VOIP\server.key"

# List to store connected clients
connected_clients = []
lock = threading.Lock()

# Function to handle a single client's audio streaming
def handle_client(client_socket):
    total_bytes_received = 0  # Initialize the variable to keep track of received bytes

    try:
        print(f"[*] New connection from {client_socket.getpeername()}")
        with lock:
            connected_clients.append(client_socket)

        p = pyaudio.PyAudio()
        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        output=True,
                        frames_per_buffer=CHUNK_SIZE)

        while True:
            data = client_socket.recv(CHUNK_SIZE)
            if not data:
                break

            total_bytes_received += len(data)  # Update the total bytes received

            # Play the received audio locally on the server using PyAudio
            stream.write(data)

        print(f"[*] Connection from {client_socket.getpeername()} closed. Total bytes received: {total_bytes_received}")

        # Send the total bytes received information back to the client
        client_socket.sendall(f"Total bytes received: {total_bytes_received}".encode())

    except ConnectionResetError:
        print(f"[*] Connection reset by {client_socket.getpeername()}")
    except Exception as e:
        print(f"Error handling client {client_socket.getpeername()}: {e}")
    finally:
        with lock:
            connected_clients.remove(client_socket)
        stream.stop_stream()
        stream.close()
        p.terminate()
        client_socket.close()

        
# Function to start the server
def start_server():
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)
    

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen()

    print(f"[*] Listening on {HOST}:{PORT}")

    try:
        with ThreadPoolExecutor(max_workers=None) as executor:
            while True:
                client_socket, addr = server_socket.accept()
                # Wrap the accepted socket with SSL
                ssl_client_socket = context.wrap_socket(client_socket, server_side=True)
                executor.submit(handle_client, ssl_client_socket)

    except KeyboardInterrupt:
        print("[*] Server shutting down.")
    finally:
        server_socket.close()

if __name__ == "_main_":
    start_server()
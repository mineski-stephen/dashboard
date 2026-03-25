import http.server
import ssl
import os
import signal
import sys

PORT = 8089
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

os.chdir(DIRECTORY)

handler = http.server.SimpleHTTPRequestHandler

context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
cert_path = os.path.join(DIRECTORY, "cert.pem")
key_path = os.path.join(DIRECTORY, "key.pem")

if not (os.path.exists(cert_path) and os.path.exists(key_path)):
    print("ERROR: cert.pem and key.pem not found!")
    print("Generate them with:")
    print('  openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes -subj "/CN=localhost"')
    exit(1)

context.load_cert_chain(cert_path, key_path)
server = http.server.ThreadingHTTPServer(("0.0.0.0", PORT), handler)
server.socket = context.wrap_socket(server.socket, server_side=True)

print(f"HTTPS server running on https://0.0.0.0:{PORT}")
print("Press Ctrl+C to stop")

try:
    server.serve_forever()
except KeyboardInterrupt:
    print("\nShutting down server...")
    server.server_close()
    sys.exit(0)
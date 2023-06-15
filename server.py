from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
import json
from simulator import Warehouse

model = Warehouse()

class Server(BaseHTTPRequestHandler):
    
    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
    def do_GET(self):
        logging.info("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
        if self.path == "/step":
            result = model.step()
            self._set_response()
            self.wfile.write(json.dumps(result).encode('utf-8'))
        else:
            self._set_response()
            self.wfile.write("Invalid endpoint".encode('utf-8'))

def run(server_class=HTTPServer, handler_class=Server, port=8585):
    logging.basicConfig(level=logging.INFO)
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    logging.info("Starting...\n") # HTTPD is HTTP Daemon!
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:   # CTRL+C stops the server
        pass
    httpd.server_close()
    logging.info("Stopping...\n")

if __name__ == '__main__':
    run()

""" 
[
    {
        "id": "23423",
        "pos": [0,1],
        "type": "rescatista"
        "display": True
    },
    ...
] 
"""
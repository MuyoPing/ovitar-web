import os
import sys

# Ensure stdout is unbuffered for Render real-time logs
sys.stdout.reconfigure(line_buffering=True)

import key_server

if __name__ == "__main__":
    key_server.init_db()
    port = int(os.environ.get("PORT", 5500))
    key_server.ThreadingHTTPServer.allow_reuse_address = True
    with key_server.ThreadingHTTPServer(("0.0.0.0", port), key_server.KeyServerHandler) as httpd:
        print(f"[OVITAR] Key Server running on 0.0.0.0:{port}", flush=True)
        httpd.serve_forever()

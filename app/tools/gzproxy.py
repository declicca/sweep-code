"""Gzip relay in front of php -S (which never compresses), so speed measures are close to production.
   python3 tools/gzproxy.py <listen_port> <upstream_port>"""
import gzip, sys, urllib.request, urllib.error
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
LISTEN, UP = int(sys.argv[1]), int(sys.argv[2])
SKIP = {'transfer-encoding', 'connection', 'content-length', 'content-encoding', 'keep-alive'}
class H(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    def log_message(self, *a): pass
    def go(self):
        n = int(self.headers.get('Content-Length') or 0); body = self.rfile.read(n) if n else None
        hd = {k: v for k, v in self.headers.items() if k.lower() not in ('host', 'accept-encoding', 'connection')}
        req = urllib.request.Request('http://127.0.0.1:%d%s' % (UP, self.path), data=body, headers=hd, method=self.command)
        class NoRedir(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *a, **k): return None
        try: r = urllib.request.build_opener(NoRedir).open(req, timeout=60)
        except urllib.error.HTTPError as e: r = e
        data = r.read(); ct = r.headers.get('Content-Type', '')
        z = 'gzip' in (self.headers.get('Accept-Encoding') or '') and len(data) > 1024 and any(t in ct for t in ('text/', 'javascript', 'json', 'svg', 'manifest'))
        if z: data = gzip.compress(data, 5)
        self.send_response(r.status)
        for k, v in r.headers.items():
            if k.lower() not in SKIP: self.send_header(k, v)
        if z: self.send_header('Content-Encoding', 'gzip')
        self.send_header('Content-Length', str(len(data))); self.end_headers(); self.wfile.write(data)
    do_GET = do_POST = do_PUT = do_DELETE = do_PATCH = go
ThreadingHTTPServer(('127.0.0.1', LISTEN), H).serve_forever()

"""Small local bridge for native SAS files used by the Atlas prototype."""
import cgi
import json
import mimetypes
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

try:
    import pyreadstat
except ImportError as error:
    pyreadstat = None
    PYREADSTAT_ERROR = str(error)

ROOT = os.path.dirname(os.path.abspath(__file__))


class AtlasHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def end_json(self, payload, status=200):
        encoded = json.dumps(payload, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(encoded)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        if self.path == "/api/health":
            self.end_json({"ok": pyreadstat is not None, "pyreadstat": getattr(pyreadstat, "__version__", None), "error": PYREADSTAT_ERROR if pyreadstat is None else None})
            return
        super().do_GET()

    def do_POST(self):
        if self.path != "/api/datasets":
            self.end_json({"error": "Unknown endpoint"}, 404)
            return
        if pyreadstat is None:
            self.end_json({"error": "Install pyreadstat first", "detail": PYREADSTAT_ERROR}, 500)
            return

        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={"REQUEST_METHOD": "POST", "CONTENT_TYPE": self.headers.get("Content-Type", "")},
        )
        datasets = []
        errors = []
        fields = form["files"] if "files" in form else []
        if not isinstance(fields, list):
            fields = [fields]
        for field in fields:
            filename = os.path.basename(field.filename or "")
            extension = os.path.splitext(filename)[1].lower()
            if extension not in {".sas7bdat", ".xpt"}:
                continue
            temporary_path = os.path.join(ROOT, ".atlas-upload-" + filename)
            try:
                with open(temporary_path, "wb") as uploaded:
                    uploaded.write(field.file.read())
                if extension == ".xpt":
                    frame, metadata = pyreadstat.read_xport(temporary_path)
                else:
                    frame, metadata = pyreadstat.read_sas7bdat(temporary_path)
                domain = os.path.splitext(filename)[0].upper()
                datasets.append({
                    "domain": domain,
                    "filename": filename,
                    "columns": [str(column).upper() for column in frame.columns],
                    "records": json.loads(frame.to_json(orient="records", date_format="iso")),
                    "label": metadata.file_label or "",
                })
            except Exception as error:
                errors.append({"filename": filename, "error": str(error)})
            finally:
                if os.path.exists(temporary_path):
                    os.remove(temporary_path)
        if not datasets and errors:
            self.end_json({"error": "No SAS datasets could be read", "files": errors}, 422)
            return
        self.end_json({"datasets": datasets, "errors": errors})


if __name__ == "__main__":
    port = int(os.environ.get("ATLAS_PORT", "8765"))
    print(f"Atlas running at http://localhost:{port}")
    ThreadingHTTPServer(("127.0.0.1", port), AtlasHandler).serve_forever()

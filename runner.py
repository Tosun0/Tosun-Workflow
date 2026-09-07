from __future__ import annotations

import argparse
import json
import mimetypes
import sys
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

import tosun_workflow as workflow


def json_bytes(payload: object) -> bytes:
    return (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    server_version = "TosunWorkflow/0.1"

    def log_message(self, format: str, *args: object) -> None:
        print(f"[GUI] {self.address_string()} - {format % args}")

    def send_json(self, payload: object, status: int = HTTPStatus.OK) -> None:
        body = json_bytes(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, path: Path) -> None:
        if not path.exists() or not path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, "file not found")
            return
        body = path.read_bytes()
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length > 2_000_000:
            raise ValueError("request too large")
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8"))

    def do_GET(self) -> None:
        try:
            parsed = urlparse(self.path)
            path = parsed.path
            if path == "/" or path == "/index.html":
                return self.send_file(workflow.WEB / "index.html")
            if path.startswith("/static/"):
                return self.send_file(workflow.safe_path(unquote(path.removeprefix("/static/")), workflow.WEB))
            if path.startswith("/docs/"):
                return self.send_file(workflow.safe_path(unquote(path.removeprefix("/docs/")), workflow.DATA_ROOT / "docs"))
            if path == "/api/health":
                return self.send_json({"ok": True, "service": "tosun-workflow", "app_root": str(workflow.ROOT), "data_root": str(workflow.DATA_ROOT)})
            if path == "/api/files":
                return self.send_json({"files": workflow.discover_files()})
            if path == "/api/projects":
                return self.send_json({"projects": workflow.list_projects()})
            if path.startswith("/api/projects/") and path.endswith("/public"):
                project_id = path.split("/")[3]
                manifest = workflow.load_manifest(project_id)
                return self.send_json({"project": manifest, "files": manifest.get("public_files", [])})
            if path.startswith("/api/projects/") and "/file/" in path:
                _, _, tail = path.partition("/api/projects/")
                project_id, _, relative = tail.partition("/file/")
                project_root = workflow.project_dir(project_id)
                return self.send_file(workflow.safe_path(unquote(relative), project_root))
            if path.startswith("/api/projects/"):
                project_id = path.removeprefix("/api/projects/").strip("/")
                return self.send_json(workflow.load_manifest(project_id))
            self.send_error(HTTPStatus.NOT_FOUND, "route not found")
        except FileNotFoundError as error:
            self.send_json({"error": str(error)}, HTTPStatus.NOT_FOUND)
        except Exception as error:
            self.send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)

    def do_POST(self) -> None:
        try:
            parsed = urlparse(self.path)
            payload = self.read_body()
            path = parsed.path
            if path == "/api/projects":
                title = str(payload.get("title", "")).strip()
                input_paths = [str(item) for item in payload.get("input_paths", [])]
                if not title or not input_paths:
                    raise ValueError("title and input_paths are required")
                project_info = {
                    "duration": str(payload.get("duration", "")),
                    "resolution": str(payload.get("resolution", "")),
                    "frame_rate": str(payload.get("frame_rate", "")),
                    "aspect_ratio": str(payload.get("aspect_ratio", "")),
                }
                return self.send_json(workflow.create_project(title, input_paths, project_info), HTTPStatus.CREATED)
            if path.startswith("/api/projects/") and path.endswith("/run"):
                project_id = path.split("/")[3]
                stage = str(payload.get("stage", ""))
                return self.send_json(workflow.run_stage(project_id, stage))
            if path.startswith("/api/projects/") and path.endswith("/approve"):
                project_id = path.split("/")[3]
                return self.send_json(workflow.approve_stage(project_id, str(payload.get("stage", "")), str(payload.get("note", ""))))
            if path.startswith("/api/projects/") and path.endswith("/backup"):
                project_id = path.split("/")[3]
                backup = workflow.backup_project(project_id, str(payload.get("reason", "manual")))
                return self.send_json({"backup": backup.relative_to(workflow.WORKSPACE).as_posix()})
            self.send_error(HTTPStatus.NOT_FOUND, "route not found")
        except FileNotFoundError as error:
            self.send_json({"error": str(error)}, HTTPStatus.NOT_FOUND)
        except Exception as error:
            self.send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)


def serve(port: int) -> None:
    workflow.ensure_layout()
    server = None
    requested_port = port
    for candidate in range(requested_port, requested_port + 10):
        try:
            server = ThreadingHTTPServer(("127.0.0.1", candidate), Handler)
            port = candidate
            break
        except OSError:
            continue
    if server is None:
        raise OSError(f"No free port found from {requested_port} to {requested_port + 9}")
    url = f"http://127.0.0.1:{port}"
    print(f"Tosun Workflow GUI: {url}")
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped")
    finally:
        server.server_close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Tosun Workflow Generator")
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--encrypt-private", metavar="PATH")
    parser.add_argument("--new-project", nargs="+", metavar="VALUE")
    parser.add_argument("--duration")
    parser.add_argument("--resolution")
    parser.add_argument("--frame-rate")
    parser.add_argument("--aspect-ratio")
    parser.add_argument("--run", nargs=2, metavar=("PROJECT_ID", "STAGE"))
    parser.add_argument("--approve", nargs=2, metavar=("PROJECT_ID", "STAGE"))
    parser.add_argument("--replace", nargs=3, metavar=("PROJECT_ID", "STAGE", "FILE"))
    parser.add_argument("--backup", nargs=2, metavar=("PROJECT_ID", "REASON"))
    args = parser.parse_args()
    workflow.ensure_layout()
    if args.encrypt_private:
        destination = workflow.encrypt_private(Path(args.encrypt_private))
        print(destination)
        return 0
    if args.new_project:
        title, *paths = args.new_project
        project_info = {
            "duration": args.duration or "",
            "resolution": args.resolution or "",
            "frame_rate": args.frame_rate or "",
            "aspect_ratio": args.aspect_ratio or "",
        }
        print(json.dumps(workflow.create_project(title, paths, project_info), ensure_ascii=False, indent=2))
        return 0
    if args.run:
        print(json.dumps(workflow.run_stage(args.run[0], args.run[1]), ensure_ascii=False, indent=2))
        return 0
    if args.approve:
        print(json.dumps(workflow.approve_stage(args.approve[0], args.approve[1]), ensure_ascii=False, indent=2))
        return 0
    if args.replace:
        print(json.dumps(workflow.replace_stage_input(args.replace[0], args.replace[1], args.replace[2]), ensure_ascii=False, indent=2))
        return 0
    if args.backup:
        print(workflow.backup_project(args.backup[0], args.backup[1]))
        return 0
    serve(args.port)
    return 0


if __name__ == "__main__":
    sys.exit(main())

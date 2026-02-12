#!/usr/bin/env python3
from pathlib import Path
from typing import Any, Dict, Optional
import tempfile
import os
import socket

from flask import Flask, request, render_template_string

import sys

ROOT = Path(__file__).parent.resolve()
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from bin_xray import BinaryParser, MapFileParser, LibraryParser, DependencyGraphBuilder


def _resolve_port(default_port: int = 8000) -> int:
    configured_port = os.getenv("PORT") or os.getenv("BINXRAY_WEB_PORT")
    try:
        preferred_port = int(configured_port) if configured_port else default_port
    except ValueError:
        preferred_port = default_port

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("0.0.0.0", preferred_port))
            return preferred_port
        except OSError:
            sock.bind(("0.0.0.0", 0))
            return int(sock.getsockname()[1])

PAGE = """
<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Bin-Xray Web</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 24px; background: #f7f7f8; color: #1f2937; }
    .card { background: white; border-radius: 8px; padding: 16px; margin-bottom: 16px; border: 1px solid #e5e7eb; }
    label { display: block; font-weight: 600; margin-top: 10px; }
    input[type=text], input[type=number] { width: 100%; padding: 8px; margin-top: 4px; box-sizing: border-box; }
    .row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    button { margin-top: 14px; padding: 10px 14px; border: 0; border-radius: 6px; background: #2563eb; color: white; cursor: pointer; }
    .error { color: #b91c1c; font-weight: 600; }
    pre { background: #111827; color: #e5e7eb; padding: 12px; border-radius: 6px; overflow-x: auto; }
    table { border-collapse: collapse; width: 100%; }
    td, th { border: 1px solid #e5e7eb; padding: 8px; text-align: left; }
    th { background: #f3f4f6; }
  </style>
</head>
<body>
  <div class=\"card\">
    <h2>Bin-Xray Web</h2>
    <p>Same analysis engine, browser-based interface.</p>
    <form method=\"post\" action=\"/analyze\" enctype=\"multipart/form-data\"> 
      <label>Binary Path</label>
      <input type=\"text\" name=\"binary\" value=\"{{ form.binary }}\" placeholder=\"/workspaces/Bin-Xray/test_binaries/adas_camera/adas_camera.elf\" />

      <label>Or choose Binary File</label>
      <input type=\"file\" name=\"binary_file\" />

      <label>Map File Path</label>
      <input type=\"text\" name=\"map\" value=\"{{ form.map }}\" placeholder=\"/workspaces/Bin-Xray/test_binaries/adas_camera/adas_camera.map\" />

      <label>Or choose Map File</label>
      <input type=\"file\" name=\"map_file\" />

      <label>Library Directory</label>
      <input type=\"text\" name=\"libdir\" value=\"{{ form.libdir }}\" placeholder=\"/workspaces/Bin-Xray/test_binaries/adas_camera/\" />

      <div class=\"row\">
        <div>
          <label>SDK Tools Directory (optional)</label>
          <input type=\"text\" name=\"sdk_tools\" value=\"{{ form.sdk_tools }}\" />
        </div>
        <div>
          <label>Depth</label>
          <input type=\"number\" min=\"1\" max=\"20\" name=\"depth\" value=\"{{ form.depth }}\" />
        </div>
      </div>

      <label>
        <input type=\"checkbox\" name=\"show_symbols\" {% if form.show_symbols %}checked{% endif %} /> Show symbol dependencies
      </label>

      <button type=\"submit\">Analyze</button>
    </form>
  </div>

  {% if error %}
  <div class=\"card\"><div class=\"error\">{{ error }}</div></div>
  {% endif %}

  {% if result %}
  <div class=\"card\">
    <h3>Summary</h3>
    <table>
      <tr><th>Metric</th><th>Value</th></tr>
      <tr><td>Nodes</td><td>{{ result.nodes }}</td></tr>
      <tr><td>Edges</td><td>{{ result.edges }}</td></tr>
      <tr><td>Build Score</td><td>{{ result.score }} / 100 ({{ result.grade }})</td></tr>
      <tr><td>Used Objects</td><td>{{ result.details.used_objects }} / {{ result.details.total_built_objects }}</td></tr>
      <tr><td>Used Libraries</td><td>{{ result.details.used_libraries }} / {{ result.details.total_built_libraries }}</td></tr>
      <tr><td>Unused Objects</td><td>{{ result.details.unused_objects }}</td></tr>
      <tr><td>Unused Libraries</td><td>{{ result.details.unused_libraries }}</td></tr>
    </table>
  </div>

  <div class=\"card\">
    <h3>Unused Components</h3>
    <pre>{{ result.unused_text }}</pre>
  </div>
  {% endif %}
</body>
</html>
"""


def _to_bool(value: Optional[str]) -> bool:
    return value in {"on", "true", "1", "yes"}


def _form_defaults() -> Dict[str, Any]:
    default_binary = ROOT / "test_binaries" / "adas_camera" / "adas_camera.elf"
    default_map = ROOT / "test_binaries" / "adas_camera" / "adas_camera.map"
    default_libdir = ROOT / "test_binaries" / "adas_camera"

    return {
        "binary": str(default_binary) if default_binary.exists() else "",
        "map": str(default_map) if default_map.exists() else "",
        "libdir": str(default_libdir) if default_libdir.is_dir() else "",
        "sdk_tools": "",
        "depth": 5,
        "show_symbols": False,
    }


def _analyze(form: Dict[str, Any]) -> Dict[str, Any]:
    binary_path = form["binary"].strip()
    map_path = form["map"].strip()
    lib_dir = form["libdir"].strip()
    sdk_tools = form["sdk_tools"].strip() or None
    depth = int(form["depth"])
    show_symbols = bool(form["show_symbols"])

    if not binary_path and not map_path:
        raise ValueError("Please provide at least a binary or map file (path input or file upload).")

    binary_info = None
    if binary_path:
        binary_file = Path(binary_path)
        if not binary_file.exists():
            raise ValueError(f"Binary not found: {binary_path}")
        binary_info = BinaryParser(sdk_tools).parse_binary(str(binary_file))

    map_info = None
    if map_path:
        map_file = Path(map_path)
        if not map_file.exists():
            raise ValueError(f"Map file not found: {map_path}")
        map_info = MapFileParser().parse_map_file(str(map_file))

    libraries = {}
    if lib_dir:
        lib_dir_path = Path(lib_dir)
        if not lib_dir_path.is_dir():
            raise ValueError(f"Library directory not found: {lib_dir}")
        lib_parser = LibraryParser(sdk_tools)
        for child in sorted(lib_dir_path.iterdir()):
            if child.suffix in {".a", ".so", ".dll"}:
                libraries[str(child)] = lib_parser.parse_library(str(child))

    builder = DependencyGraphBuilder(max_depth=depth)
    graph = builder.build_graph(binary_info, map_info, libraries, show_symbols=show_symbols)

    score, grade, details = builder.get_build_efficiency_score()
    unused = builder.get_unused_summary()

    unused_lines = ["Unused Libraries:"]
    if unused["unused_libraries"]:
        unused_lines.extend(f"- {item}" for item in unused["unused_libraries"])
    else:
        unused_lines.append("- None")
    unused_lines.append("")
    unused_lines.append("Unused Objects:")
    if unused["unused_objects"]:
        unused_lines.extend(f"- {item}" for item in unused["unused_objects"])
    else:
        unused_lines.append("- None")

    return {
        "nodes": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
        "score": score,
        "grade": grade,
        "details": details,
        "unused_text": "\n".join(unused_lines),
    }


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/")
    def home():
        return render_template_string(PAGE, form=_form_defaults(), result=None, error=None)

    @app.post("/analyze")
    def analyze():
        form = {
            "binary": request.form.get("binary", ""),
            "map": request.form.get("map", ""),
            "libdir": request.form.get("libdir", ""),
            "sdk_tools": request.form.get("sdk_tools", ""),
            "depth": request.form.get("depth", "5"),
            "show_symbols": _to_bool(request.form.get("show_symbols")),
        }
        try:
            binary_upload = request.files.get("binary_file")
            map_upload = request.files.get("map_file")

            with tempfile.TemporaryDirectory(prefix="binxray_web_") as temp_dir:
                temp_path = Path(temp_dir)

                if binary_upload and binary_upload.filename:
                    binary_name = Path(binary_upload.filename).name or "uploaded_binary"
                    binary_temp_path = temp_path / binary_name
                    binary_upload.save(binary_temp_path)
                    form["binary"] = str(binary_temp_path)

                if map_upload and map_upload.filename:
                    map_name = Path(map_upload.filename).name or "uploaded_map"
                    map_temp_path = temp_path / map_name
                    map_upload.save(map_temp_path)
                    form["map"] = str(map_temp_path)

                result = _analyze(form)
            return render_template_string(PAGE, form=form, result=result, error=None)
        except Exception as exc:
            return render_template_string(PAGE, form=form, result=None, error=str(exc))

    return app


if __name__ == "__main__":
    app = create_app()
    port = _resolve_port(8000)
    app.run(host="0.0.0.0", port=port)

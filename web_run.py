#!/usr/bin/env python3
from pathlib import Path
from typing import Any, Dict, Optional
import os
import socket
import json

from flask import Flask, request, render_template_string

import sys

ROOT = Path(__file__).parent.resolve()
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from bin_xray import BinaryParser, MapFileParser, LibraryParser, DependencyGraphBuilder

PRESETS_FILE = ROOT / "config" / "analysis_presets.json"


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


def _replace_workspace_var(value: Optional[str]) -> str:
    if not value:
        return ""
    return value.replace('${workspaceFolder}', str(ROOT))


def _load_presets() -> Dict[str, Dict[str, Any]]:
    if not PRESETS_FILE.exists():
        return {}

    try:
        with open(PRESETS_FILE, 'r', encoding='utf-8') as f:
            raw = json.load(f)
    except Exception:
        return {}

    presets: Dict[str, Dict[str, Any]] = {}
    for name, preset in raw.items():
        if not isinstance(preset, dict):
            continue
        presets[name] = {
            "binary": _replace_workspace_var(preset.get("binary")),
            "map": _replace_workspace_var(preset.get("map")),
            "libdir": _replace_workspace_var(preset.get("libdir")),
            "sdk_tools": _replace_workspace_var(preset.get("sdk_tools")),
            "depth": preset.get("depth", 5),
            "show_symbols": bool(preset.get("show_symbols", False))
        }

    return presets

PAGE = """
<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Bin-Xray Web</title>
  <style>
        :root {
            --bg: #0b1020;
            --bg-soft: #131a2f;
            --card: #ffffff;
            --muted: #64748b;
            --text: #0f172a;
            --border: #e2e8f0;
            --brand: #2563eb;
            --brand-2: #1d4ed8;
            --ok: #059669;
            --bad: #b91c1c;
        }
        * { box-sizing: border-box; }
        body {
            margin: 0;
            font-family: Inter, Segoe UI, Arial, sans-serif;
            background: radial-gradient(1200px 500px at 20% -10%, #1e3a8a 0%, var(--bg) 55%);
            color: var(--text);
            min-height: 100vh;
        }
        .wrap {
            max-width: 1080px;
            margin: 0 auto;
            padding: 24px 16px 36px;
        }
        .hero {
            background: linear-gradient(135deg, #111827, #1e293b);
            color: #e2e8f0;
            border: 1px solid rgba(148, 163, 184, 0.2);
            border-radius: 14px;
            padding: 18px 20px;
            margin-bottom: 16px;
            box-shadow: 0 12px 30px rgba(2, 6, 23, 0.35);
        }
        .hero h2 { margin: 0 0 6px; font-size: 22px; }
        .hero p { margin: 0; color: #cbd5e1; }
        .card {
            background: var(--card);
            border-radius: 14px;
            padding: 18px;
            margin-bottom: 14px;
            border: 1px solid var(--border);
            box-shadow: 0 8px 22px rgba(15, 23, 42, 0.08);
        }
        .section-title {
            margin: 0 0 10px;
            font-size: 16px;
            color: #1e293b;
        }
        .field-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
        }
        .field-full { grid-column: 1 / -1; }
        label {
            display: block;
            font-size: 13px;
            font-weight: 600;
            color: #334155;
            margin-bottom: 6px;
        }
        .hint {
            margin-top: 5px;
            font-size: 12px;
            color: var(--muted);
        }
        input[type=text], input[type=number], input[type=file], select {
            width: 100%;
            border: 1px solid #cbd5e1;
            border-radius: 10px;
            padding: 10px 11px;
            background: #fff;
            color: #0f172a;
        }
        input:focus {
            outline: none;
            border-color: #60a5fa;
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15);
        }
        .row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
        .toggle {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            margin-top: 8px;
            color: #334155;
            font-size: 14px;
        }
        .actions {
            display: flex;
            gap: 10px;
            align-items: center;
            margin-top: 14px;
        }
        button {
            border: 0;
            border-radius: 10px;
            padding: 10px 16px;
            font-weight: 600;
            color: #fff;
            background: linear-gradient(135deg, var(--brand), var(--brand-2));
            cursor: pointer;
            box-shadow: 0 6px 14px rgba(37, 99, 235, 0.3);
        }
        button:hover { filter: brightness(1.06); }
        .error {
            color: var(--bad);
            font-weight: 600;
            background: #fef2f2;
            border: 1px solid #fecaca;
            border-radius: 10px;
            padding: 10px 12px;
        }
        .metrics {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
            margin-bottom: 12px;
        }
        .metric {
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 10px;
            background: #f8fafc;
        }
        .metric .k { font-size: 12px; color: var(--muted); }
        .metric .v { font-size: 18px; font-weight: 700; margin-top: 4px; }
        .score { color: var(--ok); }
        .info-note {
            margin: 10px 0 14px;
            padding: 10px 12px;
            border: 1px solid #dbeafe;
            background: #eff6ff;
            border-radius: 10px;
            color: #1e3a8a;
            font-size: 13px;
            line-height: 1.45;
        }
        pre {
            background: #0f172a;
            color: #e2e8f0;
            padding: 12px;
            border-radius: 10px;
            overflow-x: auto;
            border: 1px solid #1e293b;
        }
        table { border-collapse: collapse; width: 100%; }
        td, th {
            border: 1px solid #e5e7eb;
            padding: 9px;
            text-align: left;
            font-size: 14px;
        }
        th { background: #f8fafc; }
        @media (max-width: 900px) {
            .metrics { grid-template-columns: 1fr 1fr; }
            .field-grid, .row { grid-template-columns: 1fr; }
        }
  </style>
</head>
<body>
    <div class=\"wrap\">
        <div class=\"hero\">
            <h2>Bin-Xray Web Dashboard</h2>
            <p>Modern browser UI powered by the same dependency analysis engine.</p>
        </div>

        <div class=\"card\">
            <h3 class=\"section-title\">Analysis Inputs</h3>
            <form method=\"post\" action=\"/analyze\">
                <div class=\"field-grid\">
                    <div class=\"field-full\">
                        <label>Preset Configuration</label>
                        <select id=\"presetSelect\" name=\"preset\">
                            <option value=\"\">(none)</option>
                            {% for preset_name in preset_options %}
                            <option value=\"{{ preset_name }}\" {% if form.preset == preset_name %}selected{% endif %}>{{ preset_name }}</option>
                            {% endfor %}
                        </select>
                        <div class=\"hint\">Choose a preset to load binary/map/lib settings by name.</div>
                    </div>

                    <div class=\"field-full\">
                        <label>Binary Path</label>
                        <input id=\"binaryPath\" type=\"text\" name=\"binary\" value=\"{{ form.binary }}\" placeholder=\"/workspaces/Bin-Xray/test_binaries/adas_camera/adas_camera.elf\" />
                        <div class=\"hint\">Provide absolute paths from the workspace.</div>
                    </div>

                    <div class=\"field-full\">
                        <label>Map File Path</label>
                        <input id=\"mapPath\" type=\"text\" name=\"map\" value=\"{{ form.map }}\" placeholder=\"/workspaces/Bin-Xray/test_binaries/adas_camera/adas_camera.map\" />
                    </div>

                    <div class=\"field-full\">
                        <label>Library Directory</label>
                        <input id=\"libDir\" type=\"text\" name=\"libdir\" value=\"{{ form.libdir }}\" placeholder=\"/workspaces/Bin-Xray/test_binaries/adas_camera/\" />
                    </div>

                    <div>
                        <label>SDK Tools Directory (optional)</label>
                        <input id=\"sdkTools\" type=\"text\" name=\"sdk_tools\" value=\"{{ form.sdk_tools }}\" />
                    </div>

                    <div>
                        <label>Depth</label>
                        <input id=\"depthInput\" type=\"number\" min=\"1\" max=\"20\" name=\"depth\" value=\"{{ form.depth }}\" />
                    </div>
                </div>

                <label class=\"toggle\">
                    <input id=\"showSymbols\" type=\"checkbox\" name=\"show_symbols\" {% if form.show_symbols %}checked{% endif %} />
                    Show symbol dependencies
                </label>

                <div class=\"actions\">
                    <button type=\"submit\">Analyze Dependency Graph</button>
                </div>
            </form>
        </div>

  {% if error %}
        <div class=\"card\"><div class=\"error\">{{ error }}</div></div>
  {% endif %}

  {% if result %}
        <div class=\"card\">
            <h3 class=\"section-title\">Summary</h3>
            <div class=\"metrics\">
                <div class=\"metric\"><div class=\"k\">Nodes</div><div class=\"v\">{{ result.nodes }}</div></div>
                <div class=\"metric\"><div class=\"k\">Edges</div><div class=\"v\">{{ result.edges }}</div></div>
                <div class=\"metric\"><div class=\"k\">Build Score</div><div class=\"v score\">{{ result.score }}</div></div>
                <div class=\"metric\"><div class=\"k\">Grade</div><div class=\"v\">{{ result.grade }}</div></div>
            </div>
            <div class=\"info-note\">
                <strong>Info:</strong> <strong>Nodes</strong> are components found in analysis (binary, libraries, object files). <strong>Edges</strong> are dependency links between them (for example, binary → library or object → object symbol references).
            </div>
            <table>
                <tr><th>Metric</th><th>Value</th></tr>
                <tr><td>Used Objects</td><td>{{ result.details.used_objects }} / {{ result.details.total_built_objects }}</td></tr>
                <tr><td>Used Libraries</td><td>{{ result.details.used_libraries }} / {{ result.details.total_built_libraries }}</td></tr>
                <tr><td>Unused Objects</td><td>{{ result.details.unused_objects }}</td></tr>
                <tr><td>Unused Libraries</td><td>{{ result.details.unused_libraries }}</td></tr>
            </table>
        </div>

        <div class=\"card\">
            <h3 class=\"section-title\">Unused Components</h3>
            <pre>{{ result.unused_text }}</pre>
        </div>
  {% endif %}
    </div>
</body>
<script>
    const presetData = {{ preset_data | tojson }};

    function applyPresetToForm(presetName) {
        if (!presetName || !presetData[presetName]) {
            return;
        }

        const preset = presetData[presetName];
        const binary = document.getElementById('binaryPath');
        const map = document.getElementById('mapPath');
        const libdir = document.getElementById('libDir');
        const sdkTools = document.getElementById('sdkTools');
        const depth = document.getElementById('depthInput');
        const showSymbols = document.getElementById('showSymbols');

        if (binary) binary.value = preset.binary || '';
        if (map) map.value = preset.map || '';
        if (libdir) libdir.value = preset.libdir || '';
        if (sdkTools) sdkTools.value = preset.sdk_tools || '';
        if (depth) depth.value = String(preset.depth ?? 5);
        if (showSymbols) showSymbols.checked = Boolean(preset.show_symbols);
    }

    document.addEventListener('DOMContentLoaded', () => {
        const presetSelect = document.getElementById('presetSelect');
        if (!presetSelect) return;
        presetSelect.addEventListener('change', (event) => {
            applyPresetToForm(event.target.value);
        });
    });
</script>
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
        "preset": "",
    }


def _analyze(form: Dict[str, Any]) -> Dict[str, Any]:
    binary_path = form["binary"].strip()
    map_path = form["map"].strip()
    lib_dir = form["libdir"].strip()
    sdk_tools = form["sdk_tools"].strip() or None
    depth = int(form["depth"])
    show_symbols = bool(form["show_symbols"])

    if not binary_path and not map_path:
        raise ValueError("Please provide at least a binary or map file path.")

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
        presets = _load_presets()
        form = _form_defaults()
        if "ADAS Camera" in presets:
            form.update(presets["ADAS Camera"])
            form["preset"] = "ADAS Camera"
        return render_template_string(PAGE, form=form, result=None, error=None, preset_options=sorted(presets.keys()), preset_data=presets)

    @app.post("/analyze")
    def analyze():
        form = {
            "preset": request.form.get("preset", ""),
            "binary": request.form.get("binary", ""),
            "map": request.form.get("map", ""),
            "libdir": request.form.get("libdir", ""),
            "sdk_tools": request.form.get("sdk_tools", ""),
            "depth": request.form.get("depth", "5"),
            "show_symbols": _to_bool(request.form.get("show_symbols")),
        }
        try:
            presets = _load_presets()
            preset_name = form.get("preset", "")
            if preset_name and preset_name in presets:
                selected = presets[preset_name]
                form["binary"] = selected.get("binary", "")
                form["map"] = selected.get("map", "")
                form["libdir"] = selected.get("libdir", "")
                form["sdk_tools"] = selected.get("sdk_tools", "")
                form["depth"] = str(selected.get("depth", 5))
                form["show_symbols"] = bool(selected.get("show_symbols", False))

            result = _analyze(form)
            return render_template_string(PAGE, form=form, result=result, error=None, preset_options=sorted(presets.keys()), preset_data=presets)
        except Exception as exc:
            presets = _load_presets()
            return render_template_string(PAGE, form=form, result=None, error=str(exc), preset_options=sorted(presets.keys()), preset_data=presets)

    return app


if __name__ == "__main__":
    app = create_app()
    port = _resolve_port(8000)
    app.run(host="0.0.0.0", port=port)

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
            --page-grad-start: #1e3a8a;
            --page-grad-end: var(--bg);
            --hero-start: #111827;
            --hero-end: #1e293b;
            --hero-text: #e2e8f0;
            --hero-border: rgba(148, 163, 184, 0.2);
            --hero-shadow: 0 12px 30px rgba(2, 6, 23, 0.35);
            --label: #334155;
            --input-bg: #ffffff;
            --input-border: #cbd5e1;
            --input-text: #0f172a;
            --card-shadow: 0 8px 22px rgba(15, 23, 42, 0.08);
            --metric-bg: #f8fafc;
            --info-btn-bg: #f8fafc;
            --info-btn-border: #cbd5e1;
            --info-btn-text: #334155;
            --info-btn-hover: #e2e8f0;
            --info-note-bg: #eff6ff;
            --info-note-border: #dbeafe;
            --info-note-text: #1e3a8a;
            --pre-bg: #0f172a;
            --pre-border: #1e293b;
            --table-border: #e5e7eb;
            --table-head-bg: #f8fafc;
            --author-bg-start: #dbeafe;
            --author-bg-end: #e0f2fe;
            --author-border: #bfdbfe;
            --author-text: #1e293b;
        }
        [data-theme="dark"] {
            --bg: #030712;
            --card: #0f172a;
            --text: #e2e8f0;
            --border: #334155;
            --muted: #94a3b8;
            --brand: #3b82f6;
            --brand-2: #2563eb;
            --page-grad-start: #0f172a;
            --page-grad-end: #020617;
            --hero-start: #020617;
            --hero-end: #111827;
            --hero-text: #e2e8f0;
            --hero-border: rgba(71, 85, 105, 0.5);
            --hero-shadow: 0 12px 30px rgba(0, 0, 0, 0.45);
            --label: #cbd5e1;
            --input-bg: #111827;
            --input-border: #334155;
            --input-text: #e2e8f0;
            --card-shadow: 0 8px 22px rgba(0, 0, 0, 0.35);
            --metric-bg: #111827;
            --info-btn-bg: #1f2937;
            --info-btn-border: #475569;
            --info-btn-text: #e2e8f0;
            --info-btn-hover: #334155;
            --info-note-bg: #1e293b;
            --info-note-border: #334155;
            --info-note-text: #cbd5e1;
            --pre-bg: #020617;
            --pre-border: #334155;
            --table-border: #334155;
            --table-head-bg: #1f2937;
            --author-bg-start: #1e293b;
            --author-bg-end: #1f2937;
            --author-border: #334155;
            --author-text: #e2e8f0;
        }
        * { box-sizing: border-box; }
        body {
            margin: 0;
            font-family: Inter, Segoe UI, Arial, sans-serif;
            background: radial-gradient(1200px 500px at 20% -10%, var(--page-grad-start) 0%, var(--page-grad-end) 55%);
            color: var(--text);
            min-height: 100vh;
        }
        .wrap {
            max-width: 1080px;
            margin: 0 auto;
            padding: 24px 16px 36px;
        }
        .hero {
            background: linear-gradient(135deg, var(--hero-start), var(--hero-end));
            color: var(--hero-text);
            border: 1px solid var(--hero-border);
            border-radius: 14px;
            padding: 18px 20px;
            margin-bottom: 16px;
            box-shadow: var(--hero-shadow);
        }
        .hero-head {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
        }
        .hero-actions {
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        .hero h2 { margin: 0; font-size: 22px; }
        .hero p { margin: 0; color: #cbd5e1; }
        .hero-info-btn {
            border-color: rgba(148, 163, 184, 0.45);
            background: rgba(15, 23, 42, 0.45);
            color: #e2e8f0;
        }
        .hero-info-btn:hover { background: rgba(30, 41, 59, 0.9); }
        .theme-switch {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            color: #e2e8f0;
            font-size: 12px;
            font-weight: 600;
            user-select: none;
        }
        .theme-switch input {
            display: none;
        }
        .theme-slider {
            position: relative;
            width: 42px;
            height: 22px;
            border-radius: 999px;
            border: 1px solid rgba(148, 163, 184, 0.45);
            background: rgba(15, 23, 42, 0.45);
            transition: background 0.2s ease;
            cursor: pointer;
        }
        .theme-slider::after {
            content: '';
            position: absolute;
            top: 2px;
            left: 2px;
            width: 16px;
            height: 16px;
            border-radius: 50%;
            background: #e2e8f0;
            transition: transform 0.2s ease;
        }
        .theme-switch input:checked + .theme-slider {
            background: rgba(59, 130, 246, 0.6);
        }
        .theme-switch input:checked + .theme-slider::after {
            transform: translateX(20px);
        }
        .card {
            background: var(--card);
            border-radius: 14px;
            padding: 18px;
            margin-bottom: 14px;
            border: 1px solid var(--border);
            box-shadow: var(--card-shadow);
        }
        .section-title {
            margin: 0 0 10px;
            font-size: 16px;
            color: var(--text);
        }
        .section-head {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
            margin-bottom: 10px;
        }
        .section-head .section-title {
            margin: 0;
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
            color: var(--label);
            margin-bottom: 6px;
        }
        .hint {
            margin-top: 5px;
            font-size: 12px;
            color: var(--muted);
        }
        input[type=text], input[type=number], input[type=file], select {
            width: 100%;
            border: 1px solid var(--input-border);
            border-radius: 10px;
            padding: 10px 11px;
            background: var(--input-bg);
            color: var(--input-text);
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
            color: var(--label);
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
            background: var(--metric-bg);
        }
        .metric .k { font-size: 12px; color: var(--muted); }
        .metric .v { font-size: 18px; font-weight: 700; margin-top: 4px; }
        .score { color: var(--ok); }
        .metric-head {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 6px;
        }
        .info-btn {
            width: 20px;
            height: 20px;
            border-radius: 50%;
            border: 1px solid var(--info-btn-border);
            background: var(--info-btn-bg);
            color: var(--info-btn-text);
            font-size: 12px;
            font-weight: 700;
            line-height: 1;
            padding: 0;
            cursor: pointer;
            box-shadow: none;
        }
        .info-btn:hover { background: var(--info-btn-hover); }
        .info-note {
            margin: 10px 0 14px;
            padding: 10px 12px;
            border: 1px solid var(--info-note-border);
            background: var(--info-note-bg);
            border-radius: 10px;
            color: var(--info-note-text);
            font-size: 13px;
            line-height: 1.45;
        }
        pre {
            background: var(--pre-bg);
            color: #e2e8f0;
            padding: 12px;
            border-radius: 10px;
            overflow-x: auto;
            border: 1px solid var(--pre-border);
        }
        table { border-collapse: collapse; width: 100%; }
        td, th {
            border: 1px solid var(--table-border);
            padding: 9px;
            text-align: left;
            font-size: 14px;
            vertical-align: top;
        }
        th { background: var(--table-head-bg); }
        .component-cell {
            max-height: 220px;
            overflow-y: auto;
        }
        .component-list {
            margin: 0;
            padding-left: 18px;
        }
        .component-list li {
            margin-bottom: 3px;
            word-break: break-word;
        }
            .author-card {
                text-align: center;
                color: var(--author-text);
                font-size: 14px;
                background: linear-gradient(135deg, var(--author-bg-start), var(--author-bg-end));
                border: 1px solid var(--author-border);
            }
            .author-label {
                font-weight: 700;
                margin-bottom: 4px;
                color: var(--author-text);
            }
            .author-name {
                font-weight: 600;
                margin-bottom: 6px;
                color: var(--author-text);
            }
            .author-link {
                color: var(--brand-2);
                text-decoration: none;
            }
            .author-link:hover { text-decoration: underline; }
        @media (max-width: 900px) {
            .metrics { grid-template-columns: 1fr 1fr; }
            .field-grid, .row { grid-template-columns: 1fr; }
        }
  </style>
</head>
<body>
    <div class=\"wrap\">
        <div class=\"hero\">
            <div class=\"hero-head\">
                <h2>Bin-Xray</h2>
                <div class=\"hero-actions\">
                    <label class="theme-switch" title="Toggle theme">
                        <span>Theme</span>
                        <input id="themeToggle" type="checkbox" onchange="toggleTheme()" />
                        <span class="theme-slider"></span>
                    </label>
                </div>
            </div>
        </div>
        <div class=\"card\">
            <div class=\"section-head\">
                <h3 class=\"section-title\">Analysis Inputs</h3>
                <button type=\"button\" class=\"info-btn\" title=\"About this tool\" onclick=\"showBinXrayInfo()\">i</button>
            </div>
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
            <h3 class=\"section-title\">Summary for {{ result.binary_name }}</h3>
            <div class=\"metrics\">
                <div class=\"metric\">
                    <div class=\"metric-head\">
                        <div class=\"k\">Nodes</div>
                        <button type=\"button\" class=\"info-btn\" title=\"What are nodes?\" onclick=\"showNodesInfo()\">i</button>
                    </div>
                    <div class=\"v\">{{ result.nodes }}</div>
                </div>
                <div class=\"metric\">
                    <div class=\"metric-head\">
                        <div class=\"k\">Edges</div>
                        <button type=\"button\" class=\"info-btn\" title=\"What are edges?\" onclick=\"showEdgesInfo()\">i</button>
                    </div>
                    <div class=\"v\">{{ result.edges }}</div>
                </div>
                <div class=\"metric\"><div class=\"k\">Build Score</div><div class=\"v score\">{{ result.score }}</div></div>
                <div class=\"metric\">
                    <div class=\"metric-head\">
                        <div class=\"k\">Grade</div>
                        <button type=\"button\" class=\"info-btn\" title=\"How grade is calculated\" onclick=\"showGradeInfo()\">i</button>
                    </div>
                    <div class=\"v\">{{ result.grade_short }}</div>
                </div>
            </div>
            <div class=\"info-note\">
                <strong>Info:</strong> <strong>Nodes</strong> are components found in analysis (binary, libraries, object files). <strong>Edges</strong> are dependency links between them (for example, binary → library or object → object symbol references).
            </div>
            <table>
                <tr><th>Metric</th><th>Value</th></tr>
                <tr><td>Objects</td><td>{{ result.details.used_objects }} / {{ result.details.total_built_objects }}</td></tr>
                <tr><td>Libraries</td><td>{{ result.details.used_libraries }} / {{ result.details.total_built_libraries }}</td></tr>
            </table>
        </div>

        <div class=\"card\">
            <h3 class=\"section-title\">Detailed Summary for {{ result.binary_name }}</h3>
            <table>
                <tr><th>Component Type</th><th>Used</th><th>Unused</th></tr>
                {% for row in result.component_rows %}
                <tr>
                    <td>{{ row.component_type }}</td>
                    <td>
                        {% if row.used %}
                        <div class=\"component-cell\">
                            <ul class=\"component-list\">
                                {% for item in row.used %}
                                <li>{{ item }}</li>
                                {% endfor %}
                            </ul>
                        </div>
                        {% else %}
                        None
                        {% endif %}
                    </td>
                    <td>
                        {% if row.unused %}
                        <div class=\"component-cell\">
                            <ul class=\"component-list\">
                                {% for item in row.unused %}
                                <li>{{ item }}</li>
                                {% endfor %}
                            </ul>
                        </div>
                        {% else %}
                        None
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </table>
        </div>
  {% endif %}

            <div class="card author-card">
                <div class="author-label">Author:</div>
                <div class="author-name">Vinod Kumar Neelakantam</div>
                <a class="author-link" href="https://www.linkedin.com/in/vinodneelakantam" target="_blank" rel="noopener noreferrer">https://www.linkedin.com/in/vinodneelakantam</a>
            </div>
    </div>
</body>
<script>
    const presetData = {{ preset_data | tojson }};

    function showGradeInfo() {
        const gradeGuide = [
            'Grading Scale (Build Efficiency Score):',
            'A+ : 95-100',
            'A  : 90-94.9',
            'B  : 80-89.9',
            'C  : 70-79.9',
            'D  : 60-69.9',
            'F  : 0-59.9'
        ];
        window.alert(gradeGuide.join('\\n'));
    }

    function showNodesInfo() {
        const nodesGuide = [
            'Nodes represent discovered components in analysis, such as:',
            '- Main binary',
            '- Libraries (.a/.so/.dll)',
            '- Object files',
            '- Symbol-level nodes (when enabled)'
        ];
        window.alert(nodesGuide.join('\\n'));
    }

    function showEdgesInfo() {
        const edgesGuide = [
            'Edges represent dependency relationships between nodes, such as:',
            '- Binary -> needed shared library',
            '- Library -> contained object',
            '- Object -> object symbol reference',
            '- Binary -> object/library symbol dependency'
        ];
        window.alert(edgesGuide.join('\\n'));
    }

    function showBinXrayInfo() {
        const summary = [
            'Bin-Xray is a binary dependency analyzer for embedded builds.',
            'It parses binaries, map files, and libraries to build dependency relationships.',
            'Use it to identify used vs unused objects/libraries and improve build efficiency.'
        ];
        window.alert(summary.join('\\n'));
    }

    function setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('binxray-theme', theme);
        const toggle = document.getElementById('themeToggle');
        if (toggle) {
            toggle.checked = theme === 'dark';
        }
    }

    function toggleTheme() {
        const toggle = document.getElementById('themeToggle');
        const isDark = Boolean(toggle && toggle.checked);
        setTheme(isDark ? 'dark' : 'light');
    }

    function initializeTheme() {
        const savedTheme = localStorage.getItem('binxray-theme');
        if (savedTheme === 'dark' || savedTheme === 'light') {
            setTheme(savedTheme);
            return;
        }
        const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        setTheme(prefersDark ? 'dark' : 'light');
    }

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
        initializeTheme();
        const presetSelect = document.getElementById('presetSelect');
        if (presetSelect) {
            presetSelect.addEventListener('change', (event) => {
                applyPresetToForm(event.target.value);
            });
        }
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
    binary_display_name = Path(binary_path).name if binary_path else "Selected Input"

    if not binary_path and not map_path:
        raise ValueError("Please provide at least a binary or map file path.")

    binary_info = None
    if binary_path:
        binary_file = Path(binary_path)
        if not binary_file.exists():
            raise ValueError(f"Binary not found: {binary_path}")
        binary_info = BinaryParser(sdk_tools).parse_binary(str(binary_file))
        binary_display_name = binary_info.name or binary_file.name

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

    used_libraries = sorted(
        node for node, node_type in builder.node_types.items()
        if node_type in {"library", "static_lib", "shared_lib"} and node not in builder.unused_libraries
    )
    used_objects = sorted(
        node for node, node_type in builder.node_types.items()
        if node_type == "object" and node not in builder.unused_objects
    )

    def _format_object_name(name: str) -> str:
        if ":" in name:
            lib_name, obj_name = name.split(":", 1)
            if lib_name.endswith((".a", ".so", ".dll")) and obj_name:
                return f"{lib_name} --> {obj_name}"

        if "(" in name:
            left, right = name.rsplit("(", 1)
            lib_name = left.strip()
            obj_name = right.rstrip(")").strip()
            if lib_name.endswith((".a", ".so", ".dll")) and obj_name:
                return f"{lib_name} --> {obj_name}"

        return name

    used_objects = [_format_object_name(item) for item in used_objects]
    unused_objects_formatted = [_format_object_name(item) for item in unused["unused_objects"]]

    unused_lines = ["Unused Libraries:"]
    if unused["unused_libraries"]:
        unused_lines.extend(f"- {item}" for item in unused["unused_libraries"])
    else:
        unused_lines.append("- None")
    unused_lines.append("")
    unused_lines.append("Unused Objects:")
    if unused_objects_formatted:
        unused_lines.extend(f"- {item}" for item in unused_objects_formatted)
    else:
        unused_lines.append("- None")

    return {
        "binary_name": binary_display_name,
        "nodes": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
        "score": score,
        "grade_short": grade.split(" ", 1)[0],
        "grade": grade,
        "details": details,
        "component_rows": [
            {
                "component_type": "Library",
                "used": used_libraries,
                "unused": unused["unused_libraries"],
            },
            {
                "component_type": "Object",
                "used": used_objects,
                "unused": unused_objects_formatted,
            },
        ],
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

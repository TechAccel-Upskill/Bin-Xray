#!/usr/bin/env python3
from pathlib import Path
from typing import Any, Dict, Optional
import os
import socket
import json
import csv
import io
from collections import Counter
import hashlib
import platform
import traceback
import uuid
from importlib import metadata
from urllib.parse import urlparse
from urllib.request import urlopen

from flask import Flask, request, render_template_string, jsonify
import shutil

import sys

ROOT = Path(__file__).parent.resolve()
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from bin_xray import BinaryParser, MapFileParser, LibraryParser, DependencyGraphBuilder
from async_jobs import AsyncJobStore
from object_storage import ObjectStorage

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
    # Special handling for test_binaries in Vercel deployment
    if _is_vercel_deployment() and "/test_binaries/" in value:
        # On Vercel, files are deployed under /var/task, so strip ${workspaceFolder} and prepend /var/task
        rel_path = value.replace('${workspaceFolder}', '').lstrip('/')
        return f"/var/task/{rel_path}"
    return value.replace('${workspaceFolder}', str(ROOT))


def _is_vercel_deployment() -> bool:
    """Check if running on Vercel"""
    return os.getenv("VERCEL") == "1" or os.getenv("VERCEL_ENV") is not None


def _load_presets() -> Dict[str, Dict[str, Any]]:
    """Load analysis presets.
    
    Loads only presets where the required binary/map files exist.
    This ensures the same presets are available in both local and Vercel.
    """
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
        
        # Resolve paths
        binary_path = _replace_workspace_var(preset.get("binary"))
        map_path = _replace_workspace_var(preset.get("map"))
        
        # Debug: Print file existence and size
        print(f"[DEBUG] Preset: {name}")
        print(f"[DEBUG] Binary path: {binary_path}")
        print(f"[DEBUG] Map path: {map_path}")
        if binary_path:
            print(f"[DEBUG] Binary exists: {Path(binary_path).exists()} size: {os.path.getsize(binary_path) if Path(binary_path).exists() else 'N/A'}")
        if map_path:
            print(f"[DEBUG] Map exists: {Path(map_path).exists()} size: {os.path.getsize(map_path) if Path(map_path).exists() else 'N/A'}")

        # Debug: Check tool availability
        for tool in ["nm", "readelf", "ar", "file"]:
            tool_path = shutil.which(tool)
            print(f"[DEBUG] Tool '{tool}': {tool_path if tool_path else 'NOT FOUND'}")

        # Only include preset if required files exist
        has_binary = binary_path and Path(binary_path).exists()
        has_map = map_path and Path(map_path).exists()
        
        if not (has_binary or has_map):
            continue
        
        presets[name] = {
            "binary": binary_path,
            "map": map_path,
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
            --hero-start: #eff6ff;
            --hero-end: #dbeafe;
            --hero-text: #0f172a;
            --hero-border: rgba(148, 163, 184, 0.35);
            --hero-shadow: 0 10px 24px rgba(37, 99, 235, 0.12);
            --hero-control-bg: rgba(255, 255, 255, 0.72);
            --hero-control-border: rgba(148, 163, 184, 0.55);
            --hero-control-text: #1e293b;
            --hero-control-hover: rgba(241, 245, 249, 0.95);
            --hero-toggle-knob: #ffffff;
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
            --upload-note-bg: #f1f5f9;
            --upload-note-border: #cbd5e1;
            --upload-note-text: #334155;
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
            --hero-start: #0b1220;
            --hero-end: #111827;
            --hero-text: #e2e8f0;
            --hero-border: rgba(71, 85, 105, 0.55);
            --hero-shadow: 0 12px 30px rgba(0, 0, 0, 0.45);
            --hero-control-bg: rgba(15, 23, 42, 0.5);
            --hero-control-border: rgba(100, 116, 139, 0.55);
            --hero-control-text: #e2e8f0;
            --hero-control-hover: rgba(30, 41, 59, 0.95);
            --hero-toggle-knob: #e2e8f0;
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
            --upload-note-bg: #1f2937;
            --upload-note-border: #475569;
            --upload-note-text: #cbd5e1;
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
            width: 100%;
            max-width: none;
            margin: 0;
            padding: 24px 24px 36px;
            min-height: 100vh;
        }
        .hero {
            background: linear-gradient(135deg, var(--hero-start), var(--hero-end));
            color: var(--hero-text);
            border: 1px solid var(--hero-border);
            border-radius: 14px;
            padding: 18px 20px;
            margin-bottom: 16px;
            box-shadow: var(--hero-shadow);
            backdrop-filter: blur(3px);
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
        .hero-info-btn {
            border-color: var(--hero-control-border);
            background: var(--hero-control-bg);
            color: var(--hero-control-text);
        }
        .hero-info-btn:hover { background: var(--hero-control-hover); }
        .theme-switch {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            color: var(--hero-text);
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
            border: 1px solid var(--hero-control-border);
            background: var(--hero-control-bg);
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
            background: var(--hero-toggle-knob);
            transition: transform 0.2s ease;
        }
        .theme-switch input:checked + .theme-slider {
            background: rgba(59, 130, 246, 0.6);
        }
        .theme-switch input:checked + .theme-slider::after {
            transform: translateX(20px);
        }
        .demo-badge {
            display: inline-block;
            background: linear-gradient(135deg, #fbbf24, #f59e0b);
            color: white;
            font-size: 11px;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 4px;
            margin-left: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .card {
            background: var(--card);
            border-radius: 14px;
            padding: 18px;
            margin-bottom: 14px;
            border: 1px solid var(--border);
            box-shadow: var(--card-shadow);
        }
        .top-layout {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 14px;
            align-items: stretch;
            margin-bottom: 14px;
        }
        .top-layout.fold-about {
            grid-template-columns: 1fr;
        }
        .top-layout.fold-about .profile-card {
            display: block;
            padding-top: 10px;
            padding-bottom: 10px;
        }
        .analysis-card {
            margin-bottom: 0;
            height: 100%;
            padding: 14px;
        }
        .profile-card {
            margin-bottom: 0;
            text-align: left;
            height: 100%;
            padding: 14px;
        }
        .profile-head {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 8px;
            margin-bottom: 8px;
        }
        .profile-head .section-title {
            margin: 0;
        }
        .panel-toggle-btn {
            border: 1px solid var(--input-border);
            border-radius: 999px;
            background: var(--input-bg);
            color: var(--input-text);
            width: 24px;
            height: 24px;
            padding: 0;
            font-weight: 600;
            cursor: pointer;
            box-shadow: none;
            line-height: 1;
            display: inline-flex;
            align-items: center;
            justify-content: center;
        }
        .panel-toggle-btn::before {
            content: '▾';
            font-size: 14px;
            transition: transform 0.2s ease;
        }
        .panel-toggle-btn.is-collapsed::before {
            transform: rotate(-90deg);
        }
        .panel-toggle-btn:hover {
            background: var(--metric-bg);
            filter: none;
        }
        .card-head {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 8px;
            margin-bottom: 8px;
        }
        .head-actions {
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        .clear-results-btn {
            border: 1px solid var(--brand-2);
            border-radius: 8px;
            background: linear-gradient(135deg, var(--brand), var(--brand-2));
            color: #ffffff;
            padding: 4px 10px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            box-shadow: 0 4px 10px rgba(37, 99, 235, 0.28);
        }
        .clear-results-btn:hover {
            filter: brightness(1.07);
        }
        .collapsible-head {
            cursor: pointer;
            user-select: none;
        }
        .card-head .section-title {
            margin: 0;
        }
        .sortable-th {
            white-space: nowrap;
        }
        .sortable-btn {
            border: 0;
            background: transparent;
            color: inherit;
            padding: 0;
            margin-left: 4px;
            cursor: pointer;
            font-size: 11px;
            box-shadow: none;
            line-height: 1;
        }
        .sortable-btn:hover {
            color: var(--brand-2);
            filter: none;
        }
        .collapsed-body {
            display: none;
        }
        .top-layout.fold-about .profile-head {
            margin-bottom: 0;
        }
        .top-layout.fold-about .profile-body {
            display: none;
        }
        .profile-photo-placeholder {
            width: 100%;
            max-width: 320px;
            aspect-ratio: 1 / 1;
            margin: 8px 0 12px;
            border: 1px dashed var(--border);
            border-radius: 14px;
            background: var(--metric-bg);
            color: var(--muted);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 13px;
            font-weight: 600;
        }
        .profile-photo {
            width: 100%;
            max-width: 320px;
            aspect-ratio: 1 / 1;
            margin: 8px 0 12px;
            border-radius: 50%;
            object-fit: cover;
            border: 4px solid var(--border);
            display: block;
        }
        .section-title {
            margin: 0 0 8px;
            font-size: 15px;
            color: var(--text);
        }
        .section-head {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 8px;
            margin-bottom: 8px;
        }
        .section-head .section-title {
            margin: 0;
        }
        .field-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }
        .field-full { grid-column: 1 / -1; }
        label {
            display: block;
            font-size: 12px;
            font-weight: 600;
            color: var(--label);
            margin-bottom: 4px;
        }
        .hint {
            margin-top: 4px;
            font-size: 11px;
            color: var(--muted);
        }
        .upload-note {
            margin-top: 8px;
            padding: 8px 10px;
            border: 1px solid var(--upload-note-border);
            background: var(--upload-note-bg);
            border-radius: 8px;
            color: var(--upload-note-text);
            font-size: 12px;
            line-height: 1.35;
        }
        input[type=text], input[type=number], input[type=file], select {
            width: 100%;
            border: 1px solid var(--input-border);
            border-radius: 8px;
            padding: 8px 10px;
            font-size: 13px;
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
            gap: 6px;
            margin-top: 6px;
            color: var(--label);
            font-size: 13px;
        }
        .actions {
            display: flex;
            gap: 10px;
            align-items: center;
            margin-top: 10px;
        }
        button {
            border: 0;
            border-radius: 8px;
            padding: 8px 14px;
            font-size: 13px;
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
        .score-bad { color: #ef4444; }
        .score-poor { color: #f97316; }
        .score-fair { color: #eab308; }
        .score-good { color: #22c55e; }
        .score-excellent { color: #10b981; }
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
            .about-title {
                font-weight: 700;
                margin-bottom: 6px;
                color: var(--author-text);
                font-size: 14px;
            }
            .about-text {
                text-align: left;
                color: var(--author-text);
                font-size: 12px;
                line-height: 1.4;
                margin-bottom: 8px;
            }
            .about-list {
                text-align: left;
                margin: 0 0 8px;
                padding-left: 18px;
                color: var(--author-text);
                font-size: 12px;
                line-height: 1.35;
            }
            .about-list li { margin-bottom: 3px; }
            .author-link {
                color: var(--brand-2);
                text-decoration: none;
                font-size: 12px;
            }
            .author-link:hover { text-decoration: underline; }
        @media (max-width: 900px) {
            .metrics { grid-template-columns: 1fr 1fr; }
            .field-grid, .row { grid-template-columns: 1fr; }
            .top-layout { grid-template-columns: 1fr; }
        }
  </style>
</head>
<body>
    <div class=\"wrap\">
        <div class=\"hero\">
            <div class=\"hero-head\">
                <h2>Bin-Xray{% if is_demo %} <span class=\"demo-badge\">Demo</span>{% endif %}</h2>
                <div class=\"hero-actions\">
                    <label class="theme-switch" title="Toggle theme">
                        <span>Theme</span>
                        <input id="themeToggle" type="checkbox" onchange="toggleTheme()" />
                        <span class="theme-slider"></span>
                    </label>
                </div>
            </div>
        </div>
        <div class=\"top-layout\">
        <div class=\"card analysis-card\">
            <div class=\"section-head\">
                <h3 class=\"section-title\">Analysis Inputs</h3>
                <button type=\"button\" class=\"info-btn\" title=\"About this tool\" onclick=\"showBinXrayInfo()\">i</button>
            </div>
            <form id=\"analyzeForm\" method=\"post\" action=\"/analyze\" enctype=\"multipart/form-data\">
                <div class=\"field-grid\">
                    <div class=\"field-full\">
                        <label>Preset Configuration</label>
                        <select id=\"presetSelect\" name=\"preset\">
                            <option value=\"__custom__\" {% if form.preset == '__custom__' %}selected{% endif %}>Custom Input (manual/upload)</option>
                            {% for preset_name in preset_options %}
                            <option value=\"{{ preset_name }}\" {% if form.preset == preset_name %}selected{% endif %}>{{ preset_name }}</option>
                            {% endfor %}
                        </select>
                        <div class=\"hint\">
                            {% if preset_options|length == 0 %}
                                {% if is_demo %}Demo binaries available: embedded_app, multi_module. Or provide your own binary path.{% else %}No presets found. Add binaries to config/analysis_presets.json.{% endif %}
                            {% else %}
                                Select a preset or manually enter paths below.
                            {% endif %}
                        </div>
                    </div>

                    <div class=\"field-full\">
                        <label>Binary Path</label>
                        <input id=\"binaryPath\" type=\"text\" name=\"binary\" value=\"{{ form.binary }}\" placeholder=\"/workspaces/Bin-Xray/test_binaries/adas_camera/adas_camera.elf\" />
                        <div class=\"hint\">Provide absolute paths from the workspace.</div>
                        <div class=\"hint\">Or upload a binary below.</div>
                        <input type=\"file\" name=\"binary_file\" accept=\".elf,.out,.axf,.bin\" />
                        <div class=\"hint\">Production (Proposal 2): use a signed download URL.</div>
                        <input type=\"text\" name=\"binary_url\" value=\"{{ form.binary_url }}\" placeholder=\"https://storage.example.com/path/to/file.elf?signature=...\" />
                    </div>

                    <div class=\"field-full\">
                        <label>Map File Path</label>
                        <input id=\"mapPath\" type=\"text\" name=\"map\" value=\"{{ form.map }}\" placeholder=\"/workspaces/Bin-Xray/test_binaries/adas_camera/adas_camera.map\" />
                        <div class=\"hint\">Or upload a map file below.</div>
                        <input type=\"file\" name=\"map_file\" accept=\".map,.txt\" />
                        <div class=\"hint\">Or provide a signed map URL.</div>
                        <input type=\"text\" name=\"map_url\" value=\"{{ form.map_url }}\" placeholder=\"https://storage.example.com/path/to/file.map?signature=...\" />
                    </div>

                    <div class=\"field-full\">
                        <label>Library Directory</label>
                        <input id=\"libDir\" type=\"text\" name=\"libdir\" value=\"{{ form.libdir }}\" placeholder=\"/workspaces/Bin-Xray/test_binaries/adas_camera/\" />
                        <div class=\"hint\">Or upload one or more library/object files.</div>
                        <input type=\"file\" name=\"lib_files\" multiple accept=\".a,.so,.dll,.o,.obj\" />
                        <div class=\"hint\">Or provide signed URLs (comma-separated or one per line).</div>
                        <input type=\"text\" name=\"lib_urls\" value=\"{{ form.lib_urls }}\" placeholder=\"https://.../liba.a?... , https://.../libb.a?...\" />
                        <div class=\"upload-note\">Uploaded files are stored in temporary server storage and used only for analysis.</div>
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
                    <button type=\"submit\">Generate Bin-Xray</button>
                </div>
            </form>
        </div>
        <div class=\"card profile-card\">
            <div id="aboutHead" class="profile-head collapsible-head">
                <h3 class="section-title">About Me</h3>
                <button id="aboutToggleBtn" type="button" class="panel-toggle-btn" onclick="toggleAboutMeFold()" aria-expanded="true" aria-label="Toggle About Me"></button>
            </div>
            <div class="profile-body">
            <img class=\"profile-photo\" src=\"{{ url_for('static', filename='profile.png') }}\" alt=\"Vinod Kumar Neelakantam\" onerror=\"this.style.display='none'; this.nextElementSibling.style.display='flex';\" />
            <div class=\"profile-photo-placeholder\" style=\"display:none;\">Place image at static/profile.png</div>
            <div class="about-text">
                I am Vinod Kumar Neelakantam, an accomplished engineering professional with over 12 years of progressive experience in embedded systems, software integration, release management, and DevOps. With a Master’s degree in Embedded &amp; VLSI Design Systems and a Certified ISTQB Tester credential, I bring a robust technical foundation and a collaborative approach to driving innovation. My diversified roles in embedded systems over a decade position me as a strong candidate in the AI era, and I am eager to contribute my expertise to your organization.
            </div>
            <div class="about-title">Embedded Trainer</div>
            <ul class="about-list">
                <li>Educated engineers on 8/16 microcontroller architectures, I/O, and peripheral design.</li>
                <li>Transformed student concepts into prototypes, bridging academia and industry.</li>
                <li>Built application and device drivers (UART, I2C, SPI, CAN) using C, C++, and assembly for hardware integration.</li>
            </ul>
            <div class="about-title">Software Integrator &amp; Release Manager</div>
            <ul class="about-list">
                <li>Validated architectural components with test-driven development (TDD).</li>
                <li>Developed integration procedures, smoke tests, and configuration documents.</li>
                <li>Coordinated global release chains across teams, aligning with project goals.</li>
                <li>Led ASPICE audits, achieving top ratings, and conducted GAP analysis for third-party assessments.</li>
            </ul>
            <div class="about-title">DevOps Platform Engineer</div>
            <ul class="about-list">
                <li>Designed automated toolchains for product life cycles, leveraging embedded expertise and ASPICE standards.</li>
            </ul>
            <div class="about-text">
                My career began as an Embedded Trainer, establishing a foundation in microcontroller systems. I then advanced to developing embedded software, mastering device drivers and hardware integration. As a Software Integrator, I focused on testing and documentation for quality assurance. Progressing to Release Manager, I managed global releases with ASPICE compliance. Now, as a DevOps Engineer, I create seamless CI/CD pipelines, optimizing workflows for the AI-driven future.
            </div>
            <a class=\"author-link\" href=\"https://www.linkedin.com/in/vinodneelakantam\" target=\"_blank\" rel=\"noopener noreferrer\">https://www.linkedin.com/in/vinodneelakantam</a>
            </div>
        </div>
        </div>

  {% if error %}
        <div class=\"card\"><div class=\"error\">{{ error }}</div></div>
  {% endif %}

  {% if result %}
        <div id="resultSections">
        <div class=\"card\">
            <div id="summaryHead" class="card-head collapsible-head">
                <h3 class=\"section-title\">Summary for {{ result.binary_name }}</h3>
                <div class="head-actions">
                    <button type="button" class="clear-results-btn" onclick="clearResultSections()" aria-label="Clear Summary and Detailed Summary">Clear Results</button>
                    <button id="summaryToggleBtn" type="button" class="panel-toggle-btn" onclick="toggleSectionBody('summaryBody','summaryToggleBtn','binxray-collapse-summary')" aria-expanded="true" aria-label="Toggle Summary"></button>
                </div>
            </div>
            <div id="summaryBody">
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
                <div class=\"metric\"><div class=\"k\">Build Score</div><div class=\"v score-{{ result.score_level }}\">{{ result.score }}</div></div>
                <div class=\"metric\">
                    <div class=\"metric-head\">
                        <div class=\"k\">Grade</div>
                        <button type=\"button\" class=\"info-btn\" title=\"How grade is calculated\" onclick=\"showGradeInfo()\">i</button>
                    </div>
                    <div class=\"v score-{{ result.score_level }}\">{{ result.grade_short }}</div>
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
        </div>

        <div class=\"card\">
            <div id="detailedHead" class="card-head collapsible-head">
                <h3 class=\"section-title\">Detailed Summary for {{ result.binary_name }}</h3>
                <div class="head-actions">
                    <form method="post" action="/download-detailed-csv">
                        <input type="hidden" name="preset" value="{{ form.preset }}" />
                        <input type="hidden" name="binary" value="{{ form.binary }}" />
                        <input type="hidden" name="map" value="{{ form.map }}" />
                        <input type="hidden" name="libdir" value="{{ form.libdir }}" />
                        <input type="hidden" name="sdk_tools" value="{{ form.sdk_tools }}" />
                        <input type="hidden" name="depth" value="{{ form.depth }}" />
                        <input type="hidden" name="show_symbols" value="{{ 'on' if form.show_symbols else '' }}" />
                        <button type="submit" class="clear-results-btn" aria-label="Download Detailed Summary CSV">Download CSV</button>
                    </form>
                    <button id="detailedToggleBtn" type="button" class="panel-toggle-btn" onclick="toggleSectionBody('detailedBody','detailedToggleBtn','binxray-collapse-detailed')" aria-expanded="true" aria-label="Toggle Detailed Summary"></button>
                </div>
            </div>
            <div id="detailedBody">
            <table id="detailedSummaryTable">
                <tr>
                    <th class="sortable-th">Unused Library<button type="button" class="sortable-btn" onclick="sortDetailedSummaryByColumn(0)" aria-label="Sort by unused library">⇅</button></th>
                    <th class="sortable-th">Unused Object<button type="button" class="sortable-btn" onclick="sortDetailedSummaryByColumn(1)" aria-label="Sort by unused object">⇅</button></th>
                    <th class="sortable-th">Source File<button type="button" class="sortable-btn" onclick="sortDetailedSummaryByColumn(2)" aria-label="Sort by source file">⇅</button></th>
                </tr>
                {% if result.unused_detail_rows %}
                {% for row in result.unused_detail_rows %}
                <tr class="detail-row">
                    <td>{{ row.unused_library or '-' }}</td>
                    <td>{{ row.unused_object or '-' }}</td>
                    <td>{{ row.source_file or '-' }}</td>
                </tr>
                {% endfor %}
                {% else %}
                <tr><td colspan="3">None</td></tr>
                {% endif %}
            </table>
            </div>
        </div>
        </div>
  {% endif %}

  {% if elf_debug_info %}
        <div class="card debug-section">
            <details>
                <summary class="section-title">ELF Debug Info</summary>
                <pre class="debug">{{ elf_debug_info }}</pre>
            </details>
        </div>
  {% endif %}

    </div>
</body>
<script>
    const presetData = {{ preset_data | tojson }};
    const hasResult = {{ 'true' if result else 'false' }};
    const detailedSortState = { column: -1, asc: true };

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

        setTheme('light');
    }

    function applyAboutMeFold() {
        const topLayout = document.querySelector('.top-layout');
        if (!topLayout) return;

        const shouldFold = localStorage.getItem('binxray-fold-about') === '1';
        topLayout.classList.toggle('fold-about', shouldFold);

        const aboutToggleBtn = document.getElementById('aboutToggleBtn');
        updateToggleButtonState(aboutToggleBtn, shouldFold);

        if (!hasResult) {
            localStorage.removeItem('binxray-fold-about');
        }
    }

    function toggleAboutMeFold() {
        const topLayout = document.querySelector('.top-layout');
        if (!topLayout) return;

        const isFolded = topLayout.classList.contains('fold-about');
        localStorage.setItem('binxray-fold-about', isFolded ? '0' : '1');
        applyAboutMeFold();
    }

    function updateToggleButtonState(toggleButton, isCollapsed) {
        if (!toggleButton) return;
        toggleButton.classList.toggle('is-collapsed', isCollapsed);
        toggleButton.setAttribute('aria-expanded', isCollapsed ? 'false' : 'true');
    }

    function updateSectionToggleButton(buttonId, isCollapsed) {
        const toggleButton = document.getElementById(buttonId);
        updateToggleButtonState(toggleButton, isCollapsed);
    }

    function toggleSectionBody(bodyId, buttonId, storageKey) {
        const sectionBody = document.getElementById(bodyId);
        if (!sectionBody) return;

        const isCollapsed = sectionBody.classList.toggle('collapsed-body');
        localStorage.setItem(storageKey, isCollapsed ? '1' : '0');
        updateSectionToggleButton(buttonId, isCollapsed);
    }

    function initializeResultSectionToggles() {
        const sections = [
            { bodyId: 'summaryBody', buttonId: 'summaryToggleBtn', key: 'binxray-collapse-summary' },
            { bodyId: 'detailedBody', buttonId: 'detailedToggleBtn', key: 'binxray-collapse-detailed' },
        ];

        sections.forEach((section) => {
            const sectionBody = document.getElementById(section.bodyId);
            if (!sectionBody) return;

            const shouldCollapse = localStorage.getItem(section.key) === '1';
            sectionBody.classList.toggle('collapsed-body', shouldCollapse);
            updateSectionToggleButton(section.buttonId, shouldCollapse);
        });
    }

    function sortDetailedSummaryByColumn(columnIndex) {
        const table = document.getElementById('detailedSummaryTable');
        if (!table) return;

        const rows = Array.from(table.querySelectorAll('tr.detail-row'));
        if (!rows.length) return;

        if (detailedSortState.column === columnIndex) {
            detailedSortState.asc = !detailedSortState.asc;
        } else {
            detailedSortState.column = columnIndex;
            detailedSortState.asc = true;
        }

        rows.sort((rowA, rowB) => {
            const textA = (rowA.children[columnIndex]?.textContent || '').trim().toLowerCase();
            const textB = (rowB.children[columnIndex]?.textContent || '').trim().toLowerCase();

            if (textA === textB) return 0;
            if (detailedSortState.asc) {
                return textA > textB ? 1 : -1;
            }
            return textA < textB ? 1 : -1;
        });

        rows.forEach((row) => table.appendChild(row));
    }

    function clearResultSections() {
        const resultSections = document.getElementById('resultSections');
        if (!resultSections) return;

        resultSections.style.display = 'none';
        localStorage.removeItem('binxray-collapse-summary');
        localStorage.removeItem('binxray-collapse-detailed');
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
        applyAboutMeFold();
        initializeResultSectionToggles();

        const bindHeadToggle = (headId, toggleFn) => {
            const head = document.getElementById(headId);
            if (!head) return;
            head.addEventListener('click', (event) => {
                if (event.target instanceof HTMLElement && event.target.closest('button')) {
                    return;
                }
                toggleFn();
            });
        };

        bindHeadToggle('aboutHead', toggleAboutMeFold);
        bindHeadToggle('summaryHead', () => toggleSectionBody('summaryBody','summaryToggleBtn','binxray-collapse-summary'));
        bindHeadToggle('detailedHead', () => toggleSectionBody('detailedBody','detailedToggleBtn','binxray-collapse-detailed'));

        const analyzeForm = document.getElementById('analyzeForm');
        if (analyzeForm) {
            analyzeForm.addEventListener('submit', () => {
                localStorage.removeItem('binxray-fold-about');
            });
        }

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
        "binary_url": "",
        "map_url": "",
        "lib_urls": "",
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
    parser_tools: Dict[str, str] = {}
    if binary_path:
        binary_file = Path(binary_path)
        if not binary_file.exists():
            raise ValueError(f"Binary not found: {binary_path}")
        parser = BinaryParser(sdk_tools)
        parser_tools = dict(parser.tools)
        binary_info = parser.parse_binary(str(binary_file))
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

    if score >= 95:
        score_level = "excellent"
    elif score >= 80:
        score_level = "good"
    elif score >= 70:
        score_level = "fair"
    elif score >= 60:
        score_level = "poor"
    else:
        score_level = "bad"

    used_libraries = sorted(
        node for node, node_type in builder.node_types.items()
        if node_type in {"library", "static_lib", "shared_lib"} and node not in builder.unused_libraries
    )
    used_objects = sorted(
        node for node, node_type in builder.node_types.items()
        if node_type == "object" and node not in builder.unused_objects
    )

    source_index: Dict[str, list[Path]] = {}
    source_extensions = {".c", ".cc", ".cpp", ".cxx", ".s", ".S", ".asm"}
    if lib_dir:
        try:
            lib_root = Path(lib_dir)
            if lib_root.is_dir():
                for path in lib_root.rglob("*"):
                    if path.is_file() and path.suffix in source_extensions:
                        source_index.setdefault(path.stem, []).append(path)
        except Exception:
            source_index = {}

    def _extract_object_name(name: str) -> Optional[str]:
        if ":" in name:
            lib_name, obj_name = name.split(":", 1)
            if lib_name.endswith((".a", ".so", ".dll")) and obj_name:
                return Path(obj_name.strip()).name

        if "(" in name:
            left, right = name.rsplit("(", 1)
            lib_name = left.strip()
            obj_name = right.rstrip(")").strip()
            if lib_name.endswith((".a", ".so", ".dll")) and obj_name:
                return Path(obj_name).name

        file_name = Path(name.strip()).name
        if file_name.endswith((".o", ".obj")):
            return file_name

        return None

    def _resolve_source_for_object(name: str) -> Optional[str]:
        object_name = _extract_object_name(name)
        if not object_name:
            return None

        stem = Path(object_name).stem
        candidates = source_index.get(stem, [])
        if candidates:
            best = min(candidates, key=lambda p: (len(p.parts), len(str(p))))
            try:
                return str(best.relative_to(Path(lib_dir)))
            except Exception:
                return str(best)

        return f"{stem}.c"

    def _format_object_name(name: str, include_source: bool = False) -> str:
        formatted_name = name
        if ":" in name:
            lib_name, obj_name = name.split(":", 1)
            if lib_name.endswith((".a", ".so", ".dll")) and obj_name:
                formatted_name = f"{lib_name} --> {obj_name}"

        elif "(" in name:
            left, right = name.rsplit("(", 1)
            lib_name = left.strip()
            obj_name = right.rstrip(")").strip()
            if lib_name.endswith((".a", ".so", ".dll")) and obj_name:
                formatted_name = f"{lib_name} --> {obj_name}"

        if include_source:
            source_file = _resolve_source_for_object(name)
            if source_file:
                return f"{formatted_name} --> {source_file}"

        return formatted_name

    used_objects = [_format_object_name(item) for item in used_objects]
    def _parse_unused_object_parts(name: str) -> Dict[str, str]:
        library_name = ""
        object_name = ""

        if ":" in name:
            lib_name, obj_name = name.split(":", 1)
            if lib_name.endswith((".a", ".so", ".dll")) and obj_name:
                library_name = lib_name.strip()
                object_name = Path(obj_name.strip()).name

        elif "(" in name:
            left, right = name.rsplit("(", 1)
            lib_name = left.strip()
            obj_name = right.rstrip(")").strip()
            if lib_name.endswith((".a", ".so", ".dll")) and obj_name:
                library_name = lib_name
                object_name = Path(obj_name).name

        if not object_name:
            extracted = _extract_object_name(name)
            object_name = extracted or ""

        source_file = _resolve_source_for_object(name) or ""
        return {
            "unused_library": library_name,
            "unused_object": object_name,
            "source_file": source_file,
        }

    unused_detail_rows = [_parse_unused_object_parts(item) for item in sorted(unused["unused_objects"])]
    libraries_with_rows = {row["unused_library"] for row in unused_detail_rows if row["unused_library"]}
    for library_name in sorted(unused["unused_libraries"]):
        if library_name not in libraries_with_rows:
            unused_detail_rows.append({
                "unused_library": library_name,
                "unused_object": "",
                "source_file": "",
            })

    unused_detail_rows = [
        row for row in unused_detail_rows
        if any(str(row.get(key, "")).strip() for key in ("unused_library", "unused_object", "source_file"))
    ]

    unused_objects_formatted = [_format_object_name(item, include_source=True) for item in unused["unused_objects"]]

    edge_type_counts = Counter()
    for _u, _v, edge_data in graph.edges(data=True):
        edge_type_counts[str(edge_data.get("type", "unknown"))] += 1

    map_object_candidates = 0
    map_unique_object_candidates = 0
    map_symbol_xref_entries = 0
    if map_info:
        object_names = []
        for section_objects in map_info.section_map.values():
            for obj in section_objects:
                if obj:
                    object_names.append(str(obj).strip())
        map_object_candidates = len(object_names)
        map_unique_object_candidates = len(set(object_names))
        map_symbol_xref_entries = len(map_info.symbol_xref)

    library_object_total = 0
    for lib_objects in libraries.values():
        library_object_total += len(lib_objects)

    diagnostics = {
        "parser_tools": parser_tools,
        "binary": {
            "defined_symbols": len(binary_info.defined_symbols) if binary_info else 0,
            "undefined_symbols": len(binary_info.undefined_symbols) if binary_info else 0,
            "sections": len(binary_info.sections) if binary_info else 0,
            "format": binary_info.format if binary_info else "",
            "architecture": binary_info.architecture if binary_info else "",
        },
        "map": {
            "sections": len(map_info.section_map) if map_info else 0,
            "symbol_xref_entries": map_symbol_xref_entries,
            "object_entries": map_object_candidates,
            "unique_objects": map_unique_object_candidates,
        },
        "libraries": {
            "count": len(libraries),
            "objects_total": library_object_total,
        },
        "graph": {
            "nodes": graph.number_of_nodes(),
            "edges": graph.number_of_edges(),
            "edge_types": dict(edge_type_counts),
            "unused_objects": len(builder.unused_objects),
            "unused_libraries": len(builder.unused_libraries),
        },
    }

    return {
        "binary_name": binary_display_name,
        "nodes": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
        "score": score,
        "score_level": score_level,
        "grade_short": grade.split(" ", 1)[0],
        "grade": grade,
        "details": details,
        "unused_detail_rows": unused_detail_rows,
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
        "diagnostics": diagnostics,
    }


def create_app() -> Flask:
    static_folder = ROOT / "static"
    app = Flask(__name__, static_folder=str(static_folder), static_url_path="/static")
    job_store = AsyncJobStore.from_env()
    object_storage = ObjectStorage.from_env()

    def _worker_auth_ok() -> bool:
        expected = os.getenv("BINXRAY_WORKER_TOKEN", "").strip()
        if not expected:
            return True
        supplied = request.headers.get("x-worker-token", "").strip()
        if not supplied:
            auth = request.headers.get("authorization", "")
            if auth.lower().startswith("bearer "):
                supplied = auth[7:].strip()
        return supplied == expected

    def _get_form_data() -> Dict[str, Any]:
        return {
            "preset": request.form.get("preset", ""),
            "binary": request.form.get("binary", ""),
            "map": request.form.get("map", ""),
            "libdir": request.form.get("libdir", ""),
            "binary_url": request.form.get("binary_url", ""),
            "map_url": request.form.get("map_url", ""),
            "lib_urls": request.form.get("lib_urls", ""),
            "sdk_tools": request.form.get("sdk_tools", ""),
            "depth": request.form.get("depth", "5"),
            "show_symbols": _to_bool(request.form.get("show_symbols")),
        }

    def _get_request_form_data() -> Dict[str, Any]:
        # Supports both HTML form submit and JSON API submit.
        if request.is_json:
            payload = request.get_json(silent=True) or {}
            return {
                "preset": str(payload.get("preset", "")),
                "binary": str(payload.get("binary", "")),
                "map": str(payload.get("map", "")),
                "libdir": str(payload.get("libdir", "")),
                "binary_url": str(payload.get("binary_url", "")),
                "map_url": str(payload.get("map_url", "")),
                "lib_urls": str(payload.get("lib_urls", "")),
                "sdk_tools": str(payload.get("sdk_tools", "")),
                "depth": str(payload.get("depth", "5")),
                "show_symbols": bool(payload.get("show_symbols", False)),
            }
        return _get_form_data()

    def _is_http_url(value: str) -> bool:
        try:
            parsed = urlparse(value)
            return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
        except Exception:
            return False

    def _download_url_to_path(src_url: str, dest: Path) -> None:
        with urlopen(src_url, timeout=60) as resp, open(dest, "wb") as out:
            while True:
                chunk = resp.read(1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)

    def _materialize_remote_inputs(form: Dict[str, Any]) -> Dict[str, Any]:
        binary_url = str(form.get("binary_url", "")).strip()
        map_url = str(form.get("map_url", "")).strip()
        lib_urls_raw = str(form.get("lib_urls", "")).strip()

        lib_urls = [
            item.strip()
            for line in lib_urls_raw.splitlines()
            for item in line.split(",")
            if item.strip()
        ]

        has_remote = bool(binary_url or map_url or lib_urls)
        if not has_remote:
            return form

        temp_root = Path("/tmp") / "binxray_remote" / uuid.uuid4().hex
        temp_root.mkdir(parents=True, exist_ok=True)

        if binary_url:
            if not _is_http_url(binary_url):
                raise ValueError("Binary URL must be http/https")
            bin_name = Path(urlparse(binary_url).path).name or "binary_input.bin"
            bin_dest = temp_root / bin_name
            _download_url_to_path(binary_url, bin_dest)
            form["binary"] = str(bin_dest)

        if map_url:
            if not _is_http_url(map_url):
                raise ValueError("Map URL must be http/https")
            map_name = Path(urlparse(map_url).path).name or "input.map"
            map_dest = temp_root / map_name
            _download_url_to_path(map_url, map_dest)
            form["map"] = str(map_dest)

        if lib_urls:
            lib_dir = temp_root / "libs"
            lib_dir.mkdir(parents=True, exist_ok=True)
            for idx, lib_url in enumerate(lib_urls, start=1):
                if not _is_http_url(lib_url):
                    raise ValueError("Library URLs must be http/https")
                lib_name = Path(urlparse(lib_url).path).name or f"library_{idx}.a"
                lib_dest = lib_dir / lib_name
                _download_url_to_path(lib_url, lib_dest)
            form["libdir"] = str(lib_dir)

        form["preset"] = "__custom__"
        return form

    def _materialize_uploaded_inputs(form: Dict[str, Any]) -> Dict[str, Any]:
        """Persist uploaded files to /tmp and override input paths for this request."""
        files = request.files
        if not files:
            return form

        binary_upload = files.get("binary_file")
        map_upload = files.get("map_file")
        lib_uploads = files.getlist("lib_files") if hasattr(files, "getlist") else []

        has_binary = bool(binary_upload and binary_upload.filename)
        has_map = bool(map_upload and map_upload.filename)
        has_libs = any(getattr(item, "filename", "") for item in lib_uploads)

        if not (has_binary or has_map or has_libs):
            return form

        upload_root = Path("/tmp") / "binxray_uploads" / uuid.uuid4().hex
        upload_root.mkdir(parents=True, exist_ok=True)

        if has_binary:
            binary_name = Path(binary_upload.filename).name
            binary_dest = upload_root / binary_name
            binary_upload.save(str(binary_dest))
            form["binary"] = str(binary_dest)

        if has_map:
            map_name = Path(map_upload.filename).name
            map_dest = upload_root / map_name
            map_upload.save(str(map_dest))
            form["map"] = str(map_dest)

        if has_libs:
            lib_dir = upload_root / "libs"
            lib_dir.mkdir(parents=True, exist_ok=True)
            for lib_file in lib_uploads:
                if not lib_file or not lib_file.filename:
                    continue
                file_name = Path(lib_file.filename).name
                lib_dest = lib_dir / file_name
                lib_file.save(str(lib_dest))
            form["libdir"] = str(lib_dir)

        # Ensure server does not force a preset over uploaded data.
        form["preset"] = "__custom__"
        return form

    def _apply_selected_preset(form: Dict[str, Any], presets: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        preset_name = form.get("preset", "")
        if preset_name and preset_name in presets:
            selected = presets[preset_name]
            form["binary"] = selected.get("binary", "")
            form["map"] = selected.get("map", "")
            form["libdir"] = selected.get("libdir", "")
            form["sdk_tools"] = selected.get("sdk_tools", "")
            form["depth"] = str(selected.get("depth", 5))
            form["show_symbols"] = bool(selected.get("show_symbols", False))
        return form

    @app.get("/storage/config")
    def storage_config():
        return jsonify({
            "ok": True,
            "enabled": object_storage is not None,
            "provider": "s3-compatible" if object_storage else None,
        })

    @app.post("/storage/sign-upload")
    def sign_upload():
        if object_storage is None:
            return jsonify({"ok": False, "error": "Object storage is not configured"}), 503

        payload = request.get_json(silent=True) or {}
        filename = str(payload.get("filename", "")).strip() or "input.bin"
        content_type = str(payload.get("content_type", "application/octet-stream")).strip() or "application/octet-stream"
        prefix = str(payload.get("prefix", "uploads")).strip() or "uploads"

        object_key = object_storage.build_object_key(filename, prefix=prefix)
        signed = object_storage.presign_upload(object_key, content_type=content_type, expires_in=900)
        return jsonify({
            "ok": True,
            "object_key": signed.object_key,
            "upload_url": signed.upload_url,
            "download_url": signed.download_url,
            "method": "PUT",
            "expires_in": signed.expires_in,
            "headers": {"Content-Type": content_type},
        })

    @app.post("/storage/sign-download")
    def sign_download():
        if object_storage is None:
            return jsonify({"ok": False, "error": "Object storage is not configured"}), 503

        payload = request.get_json(silent=True) or {}
        object_key = str(payload.get("object_key", "")).strip()
        if not object_key:
            return jsonify({"ok": False, "error": "object_key is required"}), 400

        download_url = object_storage.presign_download(object_key, expires_in=900)
        return jsonify({"ok": True, "object_key": object_key, "download_url": download_url, "expires_in": 900})

    def _run_analysis_with_debug(form: Dict[str, Any]) -> Dict[str, Any]:
        elf_debug_lines = []
        elf_debug_lines.append(f"Python: {sys.version}")
        elf_debug_lines.append(f"Platform: {platform.platform()}")

        env_vars = [
            k for k in os.environ.keys()
            if k.upper() in ("PATH", "PYTHONPATH", "HOME", "USER", "SHELL") or k.startswith("BINXRAY")
        ]
        for k in env_vars:
            elf_debug_lines.append(f"ENV {k}: {os.environ.get(k)}")

        elf_debug_lines.append(f"CWD: {os.getcwd()}")
        libdir = form.get("libdir", "")
        if libdir and Path(libdir).is_dir():
            try:
                files = os.listdir(libdir)
                elf_debug_lines.append(f"Libdir files: {files}")
            except Exception as exc:
                elf_debug_lines.append(f"Libdir list error: {exc}")

        def sha256sum(path: str) -> str:
            try:
                with open(path, "rb") as f:
                    digest = hashlib.sha256()
                    while True:
                        chunk = f.read(8192)
                        if not chunk:
                            break
                        digest.update(chunk)
                    return digest.hexdigest()
            except Exception as exc:
                return f"error: {exc}"

        for label, path in [("Binary", form.get("binary", "")), ("Map", form.get("map", ""))]:
            if path and Path(path).is_file():
                elf_debug_lines.append(f"{label} SHA256: {sha256sum(path)}")

        if libdir and Path(libdir).is_dir():
            for file_path in Path(libdir).iterdir():
                if file_path.suffix in {".a", ".so", ".dll"}:
                    elf_debug_lines.append(f"Lib: {file_path.name} SHA256: {sha256sum(str(file_path))}")

        for pkg in ["flask", "jinja2", "werkzeug"]:
            try:
                v = metadata.version(pkg)
                elf_debug_lines.append(f"{pkg} version: {v}")
            except Exception:
                pass

        for label, path in [("Binary", form.get("binary", "")), ("Map", form.get("map", "")), ("Libdir", form.get("libdir", ""))]:
            if not path:
                continue
            p = Path(path)
            exists = p.exists()
            size = os.path.getsize(path) if exists else 0
            readable = False
            perm_issue = False
            if label == "Libdir":
                if exists and p.is_dir():
                    try:
                        os.listdir(path)
                        readable = os.access(path, os.R_OK | os.X_OK)
                    except PermissionError:
                        perm_issue = True
                        readable = False
                    except Exception:
                        readable = False
            else:
                try:
                    if exists and size > 0:
                        with open(path, "rb") as f:
                            f.read(1)
                        readable = True
                except PermissionError:
                    perm_issue = True
                    readable = False
                except Exception:
                    readable = False

            elf_debug_lines.append(
                f"{label}: {path} | Exists: {exists} | Size: {size} | Readable: {readable} | Permission Issue: {perm_issue}"
            )
            if not exists or size == 0 or not readable or perm_issue:
                elf_debug_lines.append(f"[ERROR] {label} file missing, empty, unreadable, or permission denied!")

        try:
            result = _analyze(form)
            diagnostics = result.get("diagnostics", {}) if isinstance(result, dict) else {}
            if diagnostics:
                elf_debug_lines.append("Diagnostics:")
                for key, value in diagnostics.items():
                    elf_debug_lines.append(f"{key}: {json.dumps(value, default=str)}")
            return {
                "ok": True,
                "result": result,
                "error": None,
                "debug_info": "\n".join(elf_debug_lines),
            }
        except Exception as exc:
            tb = traceback.format_exc()
            elf_debug_lines.append(f"Exception: {exc}")
            elf_debug_lines.append(f"Traceback:\n{tb}")
            print(f"Exception: {exc}\nTraceback:\n{tb}", file=sys.stderr)
            return {
                "ok": False,
                "result": None,
                "error": str(exc),
                "debug_info": "\n".join(elf_debug_lines),
            }

    @app.get("/")
    def home():
        presets = _load_presets()
        form = _form_defaults()
        # Use first available preset as default
        if presets:
            first_preset_name = sorted(presets.keys())[0]
            form.update(presets[first_preset_name])
            form["preset"] = first_preset_name
        is_demo = _is_vercel_deployment() or not (ROOT / "test_binaries").exists()
        return render_template_string(PAGE, form=form, result=None, error=None, preset_options=sorted(presets.keys()), preset_data=presets, is_demo=is_demo)

    @app.post("/analyze")
    def analyze():
        presets = _load_presets()
        form = _apply_selected_preset(_get_form_data(), presets)
        form = _materialize_uploaded_inputs(form)
        form = _materialize_remote_inputs(form)
        analysis = _run_analysis_with_debug(form)
        is_demo = _is_vercel_deployment() or not (ROOT / "test_binaries").exists()
        return render_template_string(
            PAGE,
            form=form,
            result=analysis.get("result"),
            error=analysis.get("error"),
            preset_options=sorted(presets.keys()),
            preset_data=presets,
            is_demo=is_demo,
            elf_debug_info=analysis.get("debug_info", ""),
        )

    @app.post("/jobs/submit")
    def submit_job():
        if request.files and (
            (request.files.get("binary_file") and request.files.get("binary_file").filename)
            or (request.files.get("map_file") and request.files.get("map_file").filename)
            or any(getattr(item, "filename", "") for item in request.files.getlist("lib_files"))
        ):
            return jsonify({
                "ok": False,
                "error": "File uploads are currently supported only on /analyze. For async jobs, use storage-backed paths.",
            }), 400

        presets = _load_presets()
        form = _apply_selected_preset(_get_request_form_data(), presets)
        form = _materialize_remote_inputs(form)
        try:
            int(form.get("depth", "5"))
        except Exception:
            return jsonify({"ok": False, "error": "Invalid depth"}), 400

        job = job_store.create_job(form)
        return jsonify({
            "ok": True,
            "job_id": job["id"],
            "status": job["status"],
            "poll_url": f"/jobs/{job['id']}",
            "view_url": f"/jobs/view/{job['id']}",
        })

    @app.get("/jobs/<job_id>")
    def get_job(job_id: str):
        job = job_store.get_job(job_id)
        if not job:
            return jsonify({"ok": False, "error": "Job not found"}), 404

        return jsonify({
            "ok": True,
            "id": job.get("id"),
            "status": job.get("status"),
            "created_at": job.get("created_at"),
            "updated_at": job.get("updated_at"),
            "error": job.get("error"),
            "has_result": bool(job.get("result")),
        })

    @app.route("/jobs/process-next", methods=["GET", "POST"])
    def process_next_job():
        if not _worker_auth_ok():
            return jsonify({"ok": False, "error": "Unauthorized worker"}), 401

        job = job_store.claim_next_job()
        if not job:
            return jsonify({"ok": True, "processed": False, "message": "No queued jobs"})

        analysis = _run_analysis_with_debug(job.get("form", {}))
        if analysis.get("ok"):
            job_store.mark_success(job["id"], analysis.get("result") or {}, analysis.get("debug_info", ""))
            return jsonify({"ok": True, "processed": True, "job_id": job["id"], "status": "succeeded"})

        job_store.mark_failed(job["id"], str(analysis.get("error", "Analysis failed")), analysis.get("debug_info", ""))
        return jsonify({"ok": True, "processed": True, "job_id": job["id"], "status": "failed"})

    @app.get("/jobs/view/<job_id>")
    def view_job(job_id: str):
        job = job_store.get_job(job_id)
        if not job:
            return app.response_class("Job not found", status=404, mimetype="text/plain")

        presets = _load_presets()
        form = job.get("form") or _form_defaults()
        status = job.get("status")
        result = job.get("result") if status == "succeeded" else None
        error = job.get("error")
        if status in {"queued", "running"}:
            error = f"Job {status}. Call /jobs/process-next from your worker and refresh this page."

        is_demo = _is_vercel_deployment() or not (ROOT / "test_binaries").exists()
        return render_template_string(
            PAGE,
            form=form,
            result=result,
            error=error,
            preset_options=sorted(presets.keys()),
            preset_data=presets,
            is_demo=is_demo,
            elf_debug_info=job.get("debug_info", ""),
        )

    @app.post("/download-detailed-csv")
    def download_detailed_csv():
        form = _get_form_data()
        try:
            presets = _load_presets()
            form = _apply_selected_preset(form, presets)
            result = _analyze(form)

            csv_buffer = io.StringIO()
            writer = csv.writer(csv_buffer)
            writer.writerow(["Binary", "Unused Library", "Unused Object", "Source File"])

            for row in result.get("unused_detail_rows", []):
                writer.writerow([
                    result.get("binary_name", ""),
                    row.get("unused_library", ""),
                    row.get("unused_object", ""),
                    row.get("source_file", ""),
                ])

            filename = f"binxray_detailed_summary_{result.get('binary_name', 'report').replace(' ', '_')}.csv"
            return app.response_class(
                csv_buffer.getvalue(),
                mimetype="text/csv",
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )
        except Exception as exc:
            return app.response_class(str(exc), status=400, mimetype="text/plain")

    return app

if __name__ == "__main__":
    app = create_app()
    port = _resolve_port(8000)
    app.run(host="0.0.0.0", port=port)

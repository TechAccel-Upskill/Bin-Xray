# Bin-Xray Project Structure

```
Bin-Xray/
├── web_run.py              # Flask web application (main entry point)
├── requirements.txt        # Python dependencies
├── vercel.json             # Vercel deployment config
├── runtime.txt             # Vercel Python runtime version
├── LICENSE
├── README.md
│
├── api/
│   └── index.py            # Vercel WSGI handler (imports web_run.create_app)
│
├── src/                    # Core analysis engine
│   ├── bin_xray.py         # Binary/map/library parsers + DependencyGraphBuilder
│   ├── async_jobs.py       # Async job queue (LocalFile + Upstash Redis REST)
│   └── object_storage.py   # S3-compatible signed URL support (lazy boto3)
│
├── config/
│   └── analysis_presets.json  # Named presets (ADAS Camera, etc.)
│
├── static/
│   ├── test_binaries/
│   │   └── adas_camera/    # Demo ELF + map + unused library artifacts
│   ├── VInod_Image.jpg     # Profile photo
│   └── profile.png
│
└── docs/                   # Documentation
	├── INDEX.md            # Documentation index
	├── STRUCTURE.md        # This file
	├── TOOLS_REFERENCE.md  # System tools (readelf, nm, ar, etc.)
	└── SDK_EXTENSIONS.md   # Extending parsers for custom SDKs
```

## Directory Descriptions

### `/src` — Core Engine
All analysis logic lives here. `web_run.py` imports from this package.
- **bin_xray.py** — `BinaryParser`, `MapFileParser`, `LibraryParser`, `DependencyGraphBuilder`
- **async_jobs.py** — queue abstraction; `LocalFileJobStore` for dev, `RedisRestJobStore` for Vercel
- **object_storage.py** — S3 presigned upload/download URLs; boto3 loaded lazily

### `/api` — Vercel Entry Point
Thin shim that imports and exposes `create_app()` from `web_run.py`.

### `/config` — Presets
`analysis_presets.json` maps preset names to binary/map/libdir paths used by the web UI.

### `/static` — Static Assets + Demo Data
Demo binaries for the ADAS Camera preset. Also serves profile images.

### `/docs` — Documentation
Reference documentation for tools, SDK extensions, and project structure.

## Running Locally

```bash
pip install -r requirements.txt
python web_run.py
```

Open http://localhost:8000

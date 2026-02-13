# Bin-Xray

Bin-Xray is a Python GUI tool that analyzes embedded binaries and linker map files to surface dependency usage and unused resources. It generates a readable report and an interactive dependency graph to help you reduce build size and time.

## Highlights

- Analyze ELF/.out/.axf binaries and optional .map files
- Detect unused libraries and objects
- Interactive dependency visualization
- Export report and graphs

## Quick Start

1. Install dependencies:
	```bash
	pip install -r requirements.txt
	```
2. Run the app:
	```bash
	python run.py
	```

## Documentation

- User guide: [docs/README.md](docs/README.md)
- Quickstart: [docs/QUICKSTART.md](docs/QUICKSTART.md)
- Tools reference: [docs/TOOLS_REFERENCE.md](docs/TOOLS_REFERENCE.md)

## Folder Structure

- [src/bin_xray.py](src/bin_xray.py): core analysis and UI
- [src/ui](src/ui): modern UI components
- [docs](docs): documentation

## License

See [LICENSE](LICENSE).

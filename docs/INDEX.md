# Bin-Xray Documentation Index

## Getting Started

- **[../README.md](../README.md)** — Overview, quick start, Vercel deployment, API endpoints
- **[STRUCTURE.md](STRUCTURE.md)** — Project layout and directory descriptions

## Technical Reference

- **[TOOLS_REFERENCE.md](TOOLS_REFERENCE.md)** — System tools (`readelf`, `nm`, `ar`, etc.), installation by platform, SDK-specific toolchains
- **[SDK_EXTENSIONS.md](SDK_EXTENSIONS.md)** — Extending parsers for TI Jacinto, NXP S32K, Qualcomm Hexagon, and custom map formats

## Quick Reference

| Goal | Where to look |
|------|---------------|
| Run locally | [README.md — Quick Start](../README.md#quick-start) |
| Deploy to Vercel | [README.md — Deploy on Vercel](../README.md#deploy-on-vercel) |
| Upload binaries via UI | [README.md — Object Storage](../README.md#object-storage--signed-urls-proposal-2) |
| Use async job queue | [README.md — Async Queue](../README.md#optional-async-queue-advanced) |
| Install system tools | [TOOLS_REFERENCE.md](TOOLS_REFERENCE.md#installation-by-platform) |
| Add a custom SDK parser | [SDK_EXTENSIONS.md](SDK_EXTENSIONS.md#custom-map-file-formats) |
| Understand the folder layout | [STRUCTURE.md](STRUCTURE.md) |
→ See [README.md - Export](README.md#export-capabilities)

### Symbol Conflict Resolution
1. Load map file with --cref
2. Search for symbol
3. View all references
→ Use the web app Detailed Summary and diagnostics section.

## 🚦 System Requirements

**Minimum**: Python 3.7+, 512 MB RAM, binutils  
**Recommended**: Python 3.9+, 2 GB RAM, SSD

See [PROJECT_SUMMARY.md - Requirements](PROJECT_SUMMARY.md#system-requirements)

## 📞 Support Channels

- **Documentation**: All .md files in this directory
- **Tests**: [test_installation.py](test_installation.py)
- **In-app**: Help menu

## 🎉 Ready to Start!

Choose your path:
- **New user?** → Start with [QUICKSTART.md](QUICKSTART.md)
- **Technical user?** → Read [README.md](README.md)
- **SDK developer?** → See [SDK_EXTENSIONS.md](SDK_EXTENSIONS.md)
- **Performance focus?** → Check [ALTERNATIVES.md](ALTERNATIVES.md)

---

**Last Updated**: 2026-02-11  
**Version**: 1.0  
**Total Files**: 13  
**Total Lines**: ~5,000

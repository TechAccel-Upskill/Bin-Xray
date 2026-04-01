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
2. Run the app locally:
	```bash
	python run.py
	```

## Deploy on Vercel

1. Ensure `vercel` CLI is installed and logged in.
2. Deploy from repository root:
	```bash
	vercel --prod
	```

### Demo Link

- Demo link: https://your-vercel-app.vercel.app

The repository now includes:
- `api/index.py` (WSGI handler for Flask app)
- `vercel.json` (Vercel routing and Python runtime)
- `requirements.txt` (Flask and dependencies)

## Object Storage + Signed URLs (Proposal 2)

The app supports storage-backed analysis inputs for reliable Vercel execution.
Instead of relying on in-request uploads for large artifacts, upload files to object storage and pass signed download URLs.

### Endpoints

- `GET /storage/config`: check if storage signing is configured
- `POST /storage/sign-upload`: generate signed PUT + GET URLs
- `POST /storage/sign-download`: generate signed GET URL from an object key

Request example for `POST /storage/sign-upload`:

```json
{
	"filename": "adas_camera.elf",
	"content_type": "application/octet-stream",
	"prefix": "binxray-inputs"
}
```

The response includes `upload_url`, `download_url`, and `object_key`.
Upload your file with HTTP PUT to `upload_url`, then use `download_url` in the UI URL fields.

### Analysis Endpoints

- `POST /analyze`: supports direct paths, file uploads, and signed URL inputs
- `POST /jobs/submit`: queue a job (form or JSON payload)
- `GET /jobs/<job_id>`: read job status (`queued`, `running`, `succeeded`, `failed`)
- `GET|POST /jobs/process-next`: worker endpoint that processes one queued job
- `GET /jobs/view/<job_id>`: render job result/error in the normal web UI

### Vercel Setup

Set these environment variables in Vercel Project Settings:

- `BINXRAY_S3_BUCKET`: bucket name
- `BINXRAY_S3_REGION`: bucket region (optional)
- `BINXRAY_S3_ENDPOINT`: custom endpoint for S3-compatible providers (optional)
- `BINXRAY_S3_ACCESS_KEY`: access key (if not using provider-managed IAM)
- `BINXRAY_S3_SECRET_KEY`: secret key (if not using provider-managed IAM)

- `BINXRAY_QUEUE_URL`: Upstash Redis REST URL
- `BINXRAY_QUEUE_TOKEN`: Upstash Redis REST token
- `BINXRAY_WORKER_TOKEN`: shared secret for worker endpoint auth
- `CRON_SECRET`: same value as `BINXRAY_WORKER_TOKEN` (so Vercel cron can call worker securely)

Queue variables are optional unless you are also using async jobs.

### Local Development

If `BINXRAY_QUEUE_URL` and `BINXRAY_QUEUE_TOKEN` are not set, jobs use a local file store at:

- `/tmp/binxray_jobs.json` (or `BINXRAY_LOCAL_JOB_FILE` if provided)

## Documentation

- User guide: [docs/README.md](docs/README.md)
- Quickstart: [docs/QUICKSTART.md](docs/QUICKSTART.md)
- Tools reference: [docs/TOOLS_REFERENCE.md](docs/TOOLS_REFERENCE.md)
- SDK extensions:
	- [TI Processor SDK (Jacinto TDA4VM)](docs/SDK_EXTENSIONS.md#ti-processor-sdk-jacinto-tda4vm)
	- [NXP S32K SDK](docs/SDK_EXTENSIONS.md#nxp-s32k-sdk)
	- [Qualcomm Hexagon/SNPE](docs/SDK_EXTENSIONS.md#qualcomm-hexagonsnpe)
	- [Custom Map File Formats](docs/SDK_EXTENSIONS.md#custom-map-file-formats)
	- [Adding New Binary Tools](docs/SDK_EXTENSIONS.md#adding-new-binary-tools)

## Folder Structure

- [src/bin_xray.py](src/bin_xray.py): core analysis and UI
- [src/ui](src/ui): modern UI components
- [docs](docs): documentation

## License

See [LICENSE](LICENSE).

from __future__ import annotations

import json
import os
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib import error, request


class AsyncJobStore:
    """Queue-backed async job store.

    Uses Redis REST when configured (recommended for Vercel), otherwise a local
    JSON-file fallback for development.
    """

    @staticmethod
    def from_env() -> "AsyncJobStore":
        redis_url = os.getenv("BINXRAY_QUEUE_URL", "").strip()
        redis_token = os.getenv("BINXRAY_QUEUE_TOKEN", "").strip()
        if redis_url and redis_token:
            return RedisRestJobStore(redis_url, redis_token)

        local_path = Path(os.getenv("BINXRAY_LOCAL_JOB_FILE", "/tmp/binxray_jobs.json"))
        return LocalFileJobStore(local_path)

    def create_job(self, form: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    def claim_next_job(self) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    def mark_success(self, job_id: str, result: Dict[str, Any], debug_info: str) -> None:
        raise NotImplementedError

    def mark_failed(self, job_id: str, error_text: str, debug_info: str) -> None:
        raise NotImplementedError


class LocalFileJobStore(AsyncJobStore):
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self._lock = threading.Lock()

    def _read(self) -> Dict[str, Any]:
        if not self.file_path.exists():
            return {"queue": [], "jobs": {}}
        try:
            return json.loads(self.file_path.read_text(encoding="utf-8"))
        except Exception:
            return {"queue": [], "jobs": {}}

    def _write(self, data: Dict[str, Any]) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.file_path.write_text(json.dumps(data), encoding="utf-8")

    def create_job(self, form: Dict[str, Any]) -> Dict[str, Any]:
        now = int(time.time())
        job_id = uuid.uuid4().hex
        job = {
            "id": job_id,
            "status": "queued",
            "created_at": now,
            "updated_at": now,
            "form": dict(form),
            "result": None,
            "error": None,
            "debug_info": "",
        }
        with self._lock:
            data = self._read()
            data["jobs"][job_id] = job
            data["queue"].append(job_id)
            self._write(data)
        return job

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            data = self._read()
            return data["jobs"].get(job_id)

    def claim_next_job(self) -> Optional[Dict[str, Any]]:
        with self._lock:
            data = self._read()
            queue: List[str] = data.get("queue", [])
            while queue:
                job_id = queue.pop(0)
                job = data["jobs"].get(job_id)
                if not job:
                    continue
                if job.get("status") != "queued":
                    continue
                job["status"] = "running"
                job["updated_at"] = int(time.time())
                data["jobs"][job_id] = job
                data["queue"] = queue
                self._write(data)
                return job

            data["queue"] = queue
            self._write(data)
            return None

    def mark_success(self, job_id: str, result: Dict[str, Any], debug_info: str) -> None:
        with self._lock:
            data = self._read()
            job = data["jobs"].get(job_id)
            if not job:
                return
            job["status"] = "succeeded"
            job["result"] = result
            job["error"] = None
            job["debug_info"] = debug_info
            job["updated_at"] = int(time.time())
            data["jobs"][job_id] = job
            self._write(data)

    def mark_failed(self, job_id: str, error_text: str, debug_info: str) -> None:
        with self._lock:
            data = self._read()
            job = data["jobs"].get(job_id)
            if not job:
                return
            job["status"] = "failed"
            job["result"] = None
            job["error"] = error_text
            job["debug_info"] = debug_info
            job["updated_at"] = int(time.time())
            data["jobs"][job_id] = job
            self._write(data)


class RedisRestJobStore(AsyncJobStore):
    def __init__(self, redis_url: str, redis_token: str):
        self.redis_url = redis_url.rstrip("/")
        self.redis_token = redis_token
        self.queue_key = os.getenv("BINXRAY_QUEUE_KEY", "binxray:jobs:queue")
        self.job_key_prefix = os.getenv("BINXRAY_JOB_KEY_PREFIX", "binxray:job:")

    def _exec(self, *args: str) -> Any:
        req = request.Request(
            self.redis_url,
            data=json.dumps(list(args)).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": f"Bearer {self.redis_token}",
                "Content-Type": "application/json",
            },
        )
        try:
            with request.urlopen(req, timeout=10) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
                return payload.get("result")
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"Redis REST error: {exc.code} {body}") from exc

    def _job_key(self, job_id: str) -> str:
        return f"{self.job_key_prefix}{job_id}"

    def create_job(self, form: Dict[str, Any]) -> Dict[str, Any]:
        now = int(time.time())
        job_id = uuid.uuid4().hex
        job = {
            "id": job_id,
            "status": "queued",
            "created_at": now,
            "updated_at": now,
            "form": dict(form),
            "result": None,
            "error": None,
            "debug_info": "",
        }
        self._exec("SET", self._job_key(job_id), json.dumps(job))
        self._exec("LPUSH", self.queue_key, job_id)
        return job

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        raw = self._exec("GET", self._job_key(job_id))
        if not raw:
            return None
        try:
            return json.loads(raw)
        except Exception:
            return None

    def claim_next_job(self) -> Optional[Dict[str, Any]]:
        job_id = self._exec("RPOP", self.queue_key)
        if not job_id:
            return None

        job = self.get_job(str(job_id))
        if not job:
            return None

        if job.get("status") != "queued":
            return None

        job["status"] = "running"
        job["updated_at"] = int(time.time())
        self._exec("SET", self._job_key(str(job_id)), json.dumps(job))
        return job

    def mark_success(self, job_id: str, result: Dict[str, Any], debug_info: str) -> None:
        job = self.get_job(job_id)
        if not job:
            return
        job["status"] = "succeeded"
        job["result"] = result
        job["error"] = None
        job["debug_info"] = debug_info
        job["updated_at"] = int(time.time())
        self._exec("SET", self._job_key(job_id), json.dumps(job))

    def mark_failed(self, job_id: str, error_text: str, debug_info: str) -> None:
        job = self.get_job(job_id)
        if not job:
            return
        job["status"] = "failed"
        job["result"] = None
        job["error"] = error_text
        job["debug_info"] = debug_info
        job["updated_at"] = int(time.time())
        self._exec("SET", self._job_key(job_id), json.dumps(job))

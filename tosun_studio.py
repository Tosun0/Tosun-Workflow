from __future__ import annotations

import base64
import ctypes
import ctypes.wintypes as wintypes
import hashlib
import json
import mimetypes
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


APP_ROOT = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
DEV_ROOT = APP_ROOT.parent.parent if getattr(sys, "frozen", False) and APP_ROOT.parent.name == "packaged" else APP_ROOT
DATA_ROOT = DEV_ROOT if (DEV_ROOT / "workspace").exists() else APP_ROOT
ROOT = APP_ROOT
WORKSPACE = DATA_ROOT / "workspace"
INBOX = WORKSPACE / "inbox"
PROJECTS = WORKSPACE / "projects"
BACKUPS = WORKSPACE / "backups"
EXPORTS = WORKSPACE / "exports"
INSTRUCTIONS = DATA_ROOT / "instructions"
WEB = ROOT / "web"
CONFIG = DATA_ROOT / "config"
SUPPORTED = {
    ".txt", ".md", ".markdown", ".json", ".csv", ".docx", ".pdf",
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".mp4", ".mov", ".webm",
}
STAGES = ["storyboard", "prompts", "image", "video", "remotion", "publish"]
REVIEW_GATES = ["storyboard", "image", "video", "remotion"]
STAGE_LABELS = {
    "storyboard": "스토리보드 작성",
    "prompts": "프롬프트 제작",
    "image": "이미지 생성",
    "video": "Higgsfield 영상",
    "remotion": "모션 그래픽 제작",
    "publish": "최종 공개 파일",
}
STAGE_NUMBERS = {stage: index for index, stage in enumerate(STAGES, 1)}
STAGE_INSTRUCTION_FILES = {
    "storyboard": "01-analysis.md",
    "prompts": "02-prompts.md",
    "image": "03-thumbnail.md",
    "video": "04-video.md",
    "remotion": "05-infographic.md",
    "publish": "06-publish.md",
}
OUTPUT_FILES = {"image": "thumbnail.png", "video": "video.mp4", "remotion": "infographic.mp4"}
PREVIEW_OUTPUT_FILES = {"remotion": "motion-graphics-preview.mp4"}
REQUIRED_PROJECT_FIELDS = {
    "duration": "영상 길이",
    "resolution": "영상 해상도",
    "frame_rate": "영상 프레임",
    "aspect_ratio": "화면 비율",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def safe_slug(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or "untitled"


def ensure_layout() -> None:
    for path in (INBOX, PROJECTS, BACKUPS, EXPORTS, WORKSPACE / "cache"):
        path.mkdir(parents=True, exist_ok=True)


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def validate_project_info(title: str, project_info: dict[str, Any] | None) -> dict[str, Any]:
    info = project_info or {}
    if not title.strip():
        raise ValueError("프로젝트명이 필요합니다")
    missing = [label for field, label in REQUIRED_PROJECT_FIELDS.items() if not str(info.get(field, "")).strip()]
    if missing:
        raise ValueError(f"필수 입력이 필요합니다: {', '.join(missing)}")
    return info


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_media_file(path: Path, stage: str) -> dict[str, Any]:
    if stage == "image":
        signatures = {
            ".png": (b"\x89PNG\r\n\x1a\n",),
            ".jpg": (b"\xff\xd8\xff",),
            ".jpeg": (b"\xff\xd8\xff",),
            ".webp": (b"RIFF",),
            ".gif": (b"GIF87a", b"GIF89a"),
        }
        expected = signatures.get(path.suffix.lower(), ())
        header = path.read_bytes()[:12]
        if not expected or not any(header.startswith(signature) for signature in expected):
            raise ValueError(f"invalid image file: {path.name}")
        return {"status": "success", "kind": "image", "extension": path.suffix.lower()}
    if stage in {"video", "remotion"}:
        ffprobe = shutil.which("ffprobe")
        if not ffprobe:
            return {"status": "not_run", "reason": "ffprobe is not installed"}
        result = subprocess.run(
            [ffprobe, "-v", "error", "-show_entries", "format=duration:stream=codec_name,width,height,r_frame_rate,codec_type", "-of", "json", str(path)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise ValueError(f"media decode failed: {path.name}")
        return {"status": "success", "kind": "video", "probe": json.loads(result.stdout or "{}")}
    return {"status": "not_run", "reason": f"no media validator for stage {stage}"}


def safe_path(relative: str | Path, base: Path = WORKSPACE) -> Path:
    candidate = (base / Path(relative)).resolve()
    root = base.resolve()
    if candidate != root and root not in candidate.parents:
        raise ValueError("path escapes workspace")
    return candidate


def role_for(path: Path) -> str:
    name = " ".join(part.lower() for part in path.parts)
    if any(word in name for word in ("story", "콘티", "스토리")):
        return "storyboard"
    if any(word in name for word in ("motion", "graphic", "모션", "인포")):
        return "motion_graphic"
    if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
        return "visual_reference"
    if path.suffix.lower() in {".mp4", ".mov", ".webm"}:
        return "video_reference"
    return "document"


def discover_files() -> list[dict[str, Any]]:
    ensure_layout()
    rows: list[dict[str, Any]] = []
    roots = [INBOX, PROJECTS]
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.name.startswith("."):
                continue
            if path.suffix.lower() not in SUPPORTED and path.name not in {"manifest.json"}:
                continue
            relative = path.relative_to(WORKSPACE).as_posix()
            rows.append({
                "path": relative,
                "name": path.name,
                "extension": path.suffix.lower(),
                "role": role_for(path),
                "size": path.stat().st_size,
                "modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds"),
                "mime": mimetypes.guess_type(path.name)[0] or "application/octet-stream",
                "is_input": path.is_relative_to(INBOX),
            })
    return sorted(rows, key=lambda item: (not item["is_input"], item["path"].lower()))


def project_dir(project_id: str) -> Path:
    path = safe_path(Path("projects") / project_id)
    if not path.exists() or not (path / "manifest.json").exists():
        raise FileNotFoundError(project_id)
    return path


def manifest_path(project_id: str) -> Path:
    return project_dir(project_id) / "manifest.json"


def load_manifest(project_id: str) -> dict[str, Any]:
    return read_json(manifest_path(project_id), {})


def save_manifest(manifest: dict[str, Any]) -> None:
    path = manifest_path(manifest["project_id"])
    manifest["updated_at"] = utc_now()
    write_json(path, manifest)


def append_event(project_id: str, event: str, **data: Any) -> None:
    path = project_dir(project_id) / "events.jsonl"
    payload = {"timestamp": utc_now(), "event": event, **data}
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(payload, ensure_ascii=False) + "\n")


def write_report(project_id: str, stage: str, title: str, body: str) -> Path:
    folder = project_dir(project_id) / "reports"
    folder.mkdir(exist_ok=True)
    filename = f"{project_id}__s{STAGE_NUMBERS[stage]:02d}__{stage}__v001.md"
    path = folder / filename
    path.write_text(f"# {title}\n\n생성 시각: {utc_now()}\n\n{body}\n", encoding="utf-8")
    return path


def backup_project(project_id: str, reason: str = "stage-write") -> Path:
    source = project_dir(project_id)
    destination_root = BACKUPS / project_id
    destination_root.mkdir(parents=True, exist_ok=True)
    destination = destination_root / f"{project_id}__backup__{stamp()}__{safe_slug(reason)}"
    suffix = 2
    while destination.exists():
        destination = destination_root / f"{project_id}__backup__{stamp()}__{safe_slug(reason)}__{suffix}"
        suffix += 1
    shutil.copytree(source, destination)
    files = []
    for path in destination.rglob("*"):
        if path.is_file() and path.name != "backup-manifest.json":
            files.append({
                "path": path.relative_to(destination).as_posix(),
                "sha256": hash_file(path),
                "size": path.stat().st_size,
            })
    write_json(destination / "backup-manifest.json", {
        "project_id": project_id,
        "reason": reason,
        "created_at": utc_now(),
        "files": files,
    })
    append_event(project_id, "backup_created", path=destination.relative_to(WORKSPACE).as_posix(), reason=reason)
    return destination


def create_project(title: str, input_paths: list[str], project_info: dict[str, Any] | None = None) -> dict[str, Any]:
    project_info = validate_project_info(title, project_info)
    ensure_layout()
    project_id = f"{datetime.now():%Y%m%d}_{safe_slug(title)}"
    suffix = 2
    while (PROJECTS / project_id).exists():
        project_id = f"{datetime.now():%Y%m%d}_{safe_slug(title)}-{suffix}"
        suffix += 1
    root = PROJECTS / project_id
    for folder in ("input", "artifacts", "reports", "public", "requests"):
        (root / folder).mkdir(parents=True, exist_ok=True)
    copied_inputs = []
    for raw_path in input_paths:
        source = safe_path(raw_path)
        if not source.exists() or not source.is_file():
            raise FileNotFoundError(raw_path)
        destination_name = f"source__{safe_slug(source.stem)}{source.suffix.lower()}"
        destination = root / "input" / destination_name
        if destination.exists():
            destination = root / "input" / f"source__{safe_slug(source.stem)}__{hash_file(source)[:8]}{source.suffix.lower()}"
        shutil.copy2(source, destination)
        copied_inputs.append({
            "path": destination.relative_to(root).as_posix(),
            "original_path": source.relative_to(WORKSPACE).as_posix(),
            "name": source.name,
            "role": role_for(source),
            "sha256": hash_file(destination),
            "size": destination.stat().st_size,
        })
    stages = {
        stage: {"status": "ready" if index == 0 else "blocked", "started_at": None, "completed_at": None, "report": None}
        for index, stage in enumerate(STAGES)
    }
    manifest = {
        "schema_version": 1,
        "project_id": project_id,
        "title": title.strip() or project_id,
        "project_info": {
            "purpose": "",
            "audience": "",
            "duration": "",
            "resolution": "",
            "frame_rate": "",
            "aspect_ratio": "",
            "platform": "",
            "language": "",
            "tone": "",
            **(project_info or {}),
        },
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "current_stage": "storyboard",
        "inputs": copied_inputs,
        "review_gates": REVIEW_GATES,
        "stage_inputs": {gate: [] for gate in REVIEW_GATES},
        "stages": stages,
        "public_files": [],
        "provider_status": {
            "image": "not_configured",
            "higgsfield": "not_configured",
            "remotion": "request_ready",
        },
    }
    write_json(root / "manifest.json", manifest)
    (root / "events.jsonl").write_text("", encoding="utf-8")
    append_event(project_id, "project_created", title=manifest["title"], inputs=copied_inputs)
    write_report(project_id, "storyboard", "프로젝트 생성", "입력 파일을 프로젝트 `input/`에 원본 그대로 복사했습니다. 스토리보드 단계를 시작할 수 있습니다.")
    return manifest


def text_excerpt(path: Path, limit: int = 5000) -> str:
    if path.suffix.lower() not in {".txt", ".md", ".markdown", ".csv", ".json"}:
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:limit]
    except OSError:
        return ""


def stage_input_items(manifest: dict[str, Any], stage: str) -> list[dict[str, Any]]:
    """Return the latest replacement input for a stage, or the project inputs."""
    overrides = manifest.get("stage_inputs", {}).get(stage, [])
    if overrides:
        return [overrides[-1]]
    return manifest.get("inputs", [])


def load_instruction(name: str) -> str:
    path = INSTRUCTIONS / name
    return path.read_text(encoding="utf-8") if path.exists() else ""


def run_storyboard(manifest: dict[str, Any]) -> None:
    project_id = manifest["project_id"]
    root = project_dir(project_id)
    inputs = []
    for item in stage_input_items(manifest, "storyboard"):
        path = root / item["path"]
        inputs.append({
            "name": item["name"],
            "role": item.get("role", role_for(path)),
            "path": item["path"],
            "extension": path.suffix.lower(),
            "size": path.stat().st_size,
            "text_excerpt": text_excerpt(path),
        })
    analysis = {
        "project_id": project_id,
        "content_authority": "storyboard",
        "visual_authority": "motion_graphic",
        "inputs": inputs,
        "conflicts_to_review": [],
        "instruction_sources": ["instructions/core.md", "instructions/stages/01-analysis.md"],
    }
    path = root / "artifacts" / f"{project_id}__s01__storyboard__v001.json"
    write_json(path, analysis)
    report = write_report(project_id, "storyboard", "스토리보드 작성 결과", f"입력 {len(inputs)}개를 확인했습니다.\n\n- 콘텐츠 기준: storyboard\n- 시각 기준: motion_graphic\n- 텍스트 추출 가능한 입력: {sum(bool(item['text_excerpt']) for item in inputs)}개")
    stage = manifest["stages"]["storyboard"]
    stage.update({"status": "waiting_approval", "started_at": stage.get("started_at") or utc_now(), "completed_at": utc_now(), "report": report.relative_to(root).as_posix()})
    manifest["current_stage"] = "storyboard"
    save_manifest(manifest)
    append_event(project_id, "stage_completed_waiting_approval", stage="storyboard", artifact=path.relative_to(root).as_posix())


def run_prompts(manifest: dict[str, Any]) -> None:
    project_id = manifest["project_id"]
    root = project_dir(project_id)
    analysis_files = sorted((root / "artifacts").glob("*__s01__storyboard__*.json"))
    analysis = read_json(analysis_files[-1], {}) if analysis_files else {}
    source_summary = "\n".join(f"- {item['name']} ({item['role']})" for item in analysis.get("inputs", []))
    core = load_instruction("core.md")
    stage_rules = load_instruction("stages/02-prompts.md")
    private_path = INSTRUCTIONS / "private.enc"
    private_note = "private.enc 없음"
    if private_path.exists():
        try:
            decrypt_private()
            private_note = "private.enc 로컬 지침 적용됨"
        except OSError:
            private_note = "private.enc 읽기 실패"
        except Exception:
            private_note = "private.enc 복호화 실패"
    prompts = {
        "project_id": project_id,
        "image": {"purpose": "대표 비주얼 기준점", "prompt": f"Create a clear thumbnail keyframe for: {manifest['title']}"},
        "video": {"purpose": "시간 흐름과 카메라 연출", "prompt": f"Animate the approved visual direction for: {manifest['title']}"},
        "remotion": {"data_source": "approved storyboard JSON and manifest.json", "source_of_truth": "storyboard content"},
    }
    write_json(root / "artifacts" / f"{project_id}__s02__prompts__v001.json", prompts)
    prompt_md = root / "artifacts" / f"{project_id}__s02__prompt-pack__v001.md"
    prompt_md.write_text("\n".join([
        f"# Prompt Pack — {manifest['title']}",
        "", "## Active inputs", source_summary or "- 없음",
        "", "## Applied rules", f"- {private_note}", "- instructions/core.md", "- instructions/stages/02-prompts.md",
        "", "## Image", prompts["image"]["prompt"],
        "", "## Video", prompts["video"]["prompt"],
        "", "## Remotion", json.dumps(prompts["remotion"], ensure_ascii=False),
        "", "## Rule excerpts", core.strip(), stage_rules.strip(),
    ]) + "\n", encoding="utf-8")
    report = write_report(project_id, "prompts", "프롬프트 제작 결과", "이미지·영상 프롬프트를 분리했습니다. 이 단계는 스토리보드 승인 후 자동 준비됩니다.")
    stage = manifest["stages"]["prompts"]
    stage.update({"status": "completed", "started_at": stage.get("started_at") or utc_now(), "completed_at": utc_now(), "report": report.relative_to(root).as_posix()})
    manifest["current_stage"] = "image"
    manifest["stages"]["image"]["status"] = "ready"
    save_manifest(manifest)
    append_event(project_id, "stage_completed", stage="prompts")


def run_external_request(manifest: dict[str, Any], stage: str) -> None:
    project_id = manifest["project_id"]
    root = project_dir(project_id)
    provider = {"image": "image", "video": "higgsfield", "remotion": "remotion"}[stage]
    request = {
        "project_id": project_id,
        "stage": stage,
        "provider": provider,
        "status": "waiting_external",
        "created_at": utc_now(),
        "source_manifest": "manifest.json",
        "prompt_artifact": f"artifacts/{project_id}__s02__prompts__v001.json",
        "input_overrides": manifest.get("stage_inputs", {}).get(stage, []),
        "render_phase": "preview" if stage == "remotion" else "full",
        "expected_outputs": {
            "image": ["artifacts/final/thumbnail.png"],
            "video": ["artifacts/final/video.mp4"],
            "remotion": ["artifacts/previews/motion-graphics-preview.mp4"],
        }[stage],
        "note": "Provider adapter is not configured. Attach the generated file and rerun publish when ready.",
    }
    path = root / "requests" / f"{project_id}__s{STAGE_NUMBERS[stage]:02d}__{stage}-request.json"
    write_json(path, request)
    report = write_report(project_id, stage, f"{STAGE_LABELS[stage]} 요청 준비", f"외부 provider 요청 파일을 만들었습니다: `{path.relative_to(root).as_posix()}`\n\n현재 상태: `waiting_external`\n실제 완료 파일이 확인되기 전에는 성공으로 처리하지 않습니다.")
    stage_state = manifest["stages"][stage]
    stage_state.update({"status": "waiting_external", "started_at": stage_state.get("started_at") or utc_now(), "completed_at": None, "report": report.relative_to(root).as_posix()})
    manifest["current_stage"] = stage
    save_manifest(manifest)
    append_event(project_id, "external_request_ready", stage=stage, provider=provider, request=path.relative_to(root).as_posix())


def attach_output(project_id: str, stage: str, source_path: str, render_phase: str = "full") -> dict[str, Any]:
    if stage not in OUTPUT_FILES:
        raise ValueError(f"unsupported output stage: {stage}")
    if render_phase not in {"preview", "full"} or (render_phase == "preview" and stage != "remotion"):
        raise ValueError(f"unsupported render phase: {render_phase}")
    source = Path(source_path).expanduser().resolve()
    if not source.exists() or not source.is_file():
        raise FileNotFoundError(source_path)
    validation = validate_media_file(source, stage)
    manifest = load_manifest(project_id)
    root = project_dir(project_id)
    state = manifest["stages"][stage]
    expected_status = "waiting_external"
    if stage == "remotion" and render_phase == "full":
        expected_status = "ready"
    if state.get("status") != expected_status:
        raise RuntimeError(
            "stage output cannot be attached before its request/review handoff: "
            f"{stage} ({state.get('status')}); expected {expected_status}"
        )
    backup_project(project_id, f"before-attach-{stage}")
    if render_phase == "preview":
        destination = root / "artifacts" / "previews" / PREVIEW_OUTPUT_FILES[stage]
    else:
        destination = root / "artifacts" / "final" / OUTPUT_FILES[stage]
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    state.update({"status": "waiting_approval", "completed_at": utc_now(), "output": destination.relative_to(root).as_posix(), "render_phase": render_phase, "validation": validation})
    manifest["current_stage"] = stage
    save_manifest(manifest)
    append_event(project_id, "output_attached_waiting_approval", stage=stage, output=destination.relative_to(root).as_posix())
    return manifest


def replace_stage_input(project_id: str, stage: str, source_path: str) -> dict[str, Any]:
    if stage not in REVIEW_GATES:
        raise ValueError(f"unsupported review gate: {stage}")
    source = Path(source_path).expanduser().resolve()
    if not source.exists() or not source.is_file():
        raise FileNotFoundError(source_path)
    manifest = load_manifest(project_id)
    root = project_dir(project_id)
    backup_project(project_id, f"before-replace-{stage}-input")
    destination = root / "input" / "replacements" / stage / f"{stamp()}__{safe_slug(source.stem)}{source.suffix.lower()}"
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    item = {
        "path": destination.relative_to(root).as_posix(),
        "original_path": str(source),
        "name": source.name,
        "sha256": hash_file(destination),
        "size": destination.stat().st_size,
        "replaced_at": utc_now(),
    }
    manifest.setdefault("stage_inputs", {}).setdefault(stage, []).append(item)
    for affected in STAGES[STAGES.index(stage):]:
        manifest["stages"][affected].update({"status": "blocked", "started_at": None, "completed_at": None, "report": None, "render_phase": None})
    manifest["stages"][stage]["status"] = "ready"
    manifest["current_stage"] = stage
    save_manifest(manifest)
    append_event(project_id, "stage_input_replaced", stage=stage, input=item["path"])
    return manifest


def publish(manifest: dict[str, Any]) -> None:
    project_id = manifest["project_id"]
    root = project_dir(project_id)
    public = root / "public"
    public.mkdir(exist_ok=True)
    mapping = {
        "image": ("thumbnail.png", "thumbnail.png"),
        "video": ("video.mp4", "video.mp4"),
        "remotion": ("infographic.mp4", "infographic.mp4"),
    }
    files = []
    for stage_name, (source_name, public_name) in mapping.items():
        state = manifest["stages"].get(stage_name, {})
        if state.get("status") not in {"approved", "completed"}:
            continue
        output = state.get("output")
        if not output:
            continue
        source = safe_path(output, root)
        expected = (root / "artifacts" / "final" / source_name).resolve()
        if source.resolve() != expected or not source.is_file():
            continue
        shutil.copy2(source, public / public_name)
        files.append(public_name)
    for public_name in ("thumbnail.png", "video.mp4", "infographic.mp4"):
        if public_name not in files:
            stale = public / public_name
            if stale.exists():
                stale.unlink()
    public_manifest = {
        "project_id": project_id,
        "title": manifest["title"],
        "published_at": utc_now(),
        "files": files,
        "status": "partial" if len(files) < len(mapping) else "complete",
    }
    write_json(public / "manifest.json", public_manifest)
    report = write_report(project_id, "publish", "최종 공개 파일", f"public/에 승인 파일 {len(files)}개를 수집했습니다.\n\n" + ("\n".join(f"- {item}" for item in files) or "- 아직 최종 파일 없음"))
    stage = manifest["stages"]["publish"]
    stage.update({"status": "completed" if files else "waiting_external", "started_at": stage.get("started_at") or utc_now(), "completed_at": utc_now() if files else None, "report": report.relative_to(root).as_posix()})
    manifest["public_files"] = files
    manifest["current_stage"] = "publish"
    save_manifest(manifest)
    append_event(project_id, "published", files=files)


def run_stage(project_id: str, stage: str) -> dict[str, Any]:
    if stage not in STAGES:
        raise ValueError(f"unknown stage: {stage}")
    manifest = load_manifest(project_id)
    if stage != "storyboard":
        previous = STAGES[STAGES.index(stage) - 1]
        if manifest["stages"][previous]["status"] not in {"approved", "completed"}:
            raise RuntimeError(f"previous stage is not approved: {previous}")
    try:
        backup_project(project_id, f"before-{stage}")
        state = manifest["stages"][stage]
        state["status"] = "running"
        state["started_at"] = utc_now()
        state.pop("error", None)
        state.pop("recovery", None)
        save_manifest(manifest)
        append_event(project_id, "stage_started", stage=stage)
        if stage == "storyboard":
            run_storyboard(manifest)
        elif stage == "prompts":
            run_prompts(manifest)
        elif stage in {"image", "video", "remotion"}:
            run_external_request(manifest, stage)
        elif stage == "publish":
            publish(manifest)
        return load_manifest(project_id)
    except Exception as error:
        state = manifest["stages"][stage]
        state.update({
            "status": "failed",
            "failed_at": utc_now(),
            "completed_at": None,
            "error": str(error),
            "retryable": True,
            "recovery": "원인을 수정한 뒤 같은 시퀀스를 다시 실행하거나 입력 파일을 교체하세요.",
        })
        manifest["current_stage"] = stage
        report = write_report(
            project_id,
            stage,
            f"{STAGE_LABELS[stage]} 실패",
            f"실패 원인: {error}\n\n재시도 가능: 예\n복구 방법: 원인을 수정한 뒤 현재 시퀀스를 다시 실행하세요.",
        )
        state["report"] = report.relative_to(project_dir(project_id)).as_posix()
        save_manifest(manifest)
        append_event(project_id, "stage_failed", stage=stage, error=str(error), retryable=True)
        raise


def approve_stage(project_id: str, stage: str, note: str = "") -> dict[str, Any]:
    manifest = load_manifest(project_id)
    state = manifest["stages"].get(stage)
    if state is None:
        raise ValueError(stage)
    if stage not in REVIEW_GATES:
        raise ValueError(f"only review gates can be approved: {stage}")
    if state["status"] not in {"waiting_approval", "completed"}:
        raise RuntimeError(f"stage is not reviewable: {stage} ({state['status']})")
    backup_project(project_id, f"before-approve-{stage}")
    state["status"] = "approved"
    state["approved_at"] = utc_now()
    state["approval_note"] = note
    if stage == "storyboard":
        run_prompts(manifest)
        next_stage = "image"
    elif stage == "image":
        next_stage = "video"
    elif stage == "video":
        next_stage = "remotion"
    elif stage == "remotion" and state.get("render_phase") == "preview":
        state["status"] = "ready"
        state["render_phase"] = "full"
        manifest["current_stage"] = "remotion"
        save_manifest(manifest)
        append_event(project_id, "preview_approved_ready_for_full_render", stage=stage)
        return manifest
    else:
        publish(manifest)
        next_stage = "publish"
    if next_stage != "publish" and manifest["stages"][next_stage]["status"] == "blocked":
        manifest["stages"][next_stage]["status"] = "ready"
    manifest["current_stage"] = next_stage
    save_manifest(manifest)
    append_event(project_id, "stage_approved", stage=stage, note=note)
    return manifest


def list_projects() -> list[dict[str, Any]]:
    ensure_layout()
    rows = []
    for path in sorted(PROJECTS.iterdir()):
        if path.is_dir() and (path / "manifest.json").exists():
            rows.append(read_json(path / "manifest.json", {}))
    return sorted(rows, key=lambda item: item.get("updated_at", ""), reverse=True)


class DATA_BLOB(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]


def _dpapi(data: bytes, decrypt: bool = False) -> bytes:
    if os.name != "nt":
        raise RuntimeError("DPAPI encryption is only available on Windows")
    source = DATA_BLOB(len(data), ctypes.cast(ctypes.create_string_buffer(data), ctypes.POINTER(ctypes.c_byte)))
    result = DATA_BLOB()
    function = ctypes.windll.crypt32.CryptUnprotectData if decrypt else ctypes.windll.crypt32.CryptProtectData
    ok = function(ctypes.byref(source), None, None, None, None, 0, ctypes.byref(result))
    if not ok:
        raise ctypes.WinError()
    try:
        return ctypes.string_at(result.pbData, result.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(result.pbData)


def encrypt_private(source: Path) -> Path:
    payload = source.read_bytes()
    destination = INSTRUCTIONS / "private.enc"
    destination.write_bytes(base64.b64encode(_dpapi(payload)))
    return destination


def decrypt_private() -> str:
    path = INSTRUCTIONS / "private.enc"
    if not path.exists():
        return ""
    return _dpapi(base64.b64decode(path.read_bytes()), decrypt=True).decode("utf-8", errors="replace")

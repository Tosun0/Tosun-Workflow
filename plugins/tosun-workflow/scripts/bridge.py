from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path


def resolve_project_root() -> Path:
    candidates: list[Path] = []
    configured = os.environ.get("TOSUN_WORKFLOW_ROOT")
    if configured:
        candidates.append(Path(configured).expanduser())
    plugin_root = Path(__file__).resolve().parents[1]
    candidates.append(plugin_root)
    current = Path.cwd().resolve()
    candidates.append(current)
    candidates.extend(current.parents)
    for candidate in candidates:
        if (candidate / "tosun_workflow.py").is_file() and (candidate / "workspace").is_dir():
            return candidate
    raise RuntimeError("Tosun Workflow engine is not bundled or TOSUN_WORKFLOW_ROOT is not configured")


PROJECT_ROOT = resolve_project_root()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import tosun_workflow as workflow


def compact_manifest(manifest: dict) -> dict:
    stages = manifest.get("stages", {})
    stage = manifest.get("current_stage")
    review_actions = {
        "storyboard": "show the storyboard form or draft and wait for the user's acceptance",
        "image": "generate the image, display it, and wait for the user's acceptance",
        "video": "generate the video, display it, and wait for the user's acceptance",
        "remotion": "render a fast Remotion preview first, display it, then full-render after acceptance",
    }
    return {
        "project_id": manifest.get("project_id"),
        "title": manifest.get("title"),
        "project_info": manifest.get("project_info", {}),
        "current_stage": stage,
        "current_status": stages.get(stage, {}).get("status"),
        "review_gates": manifest.get("review_gates", workflow.REVIEW_GATES),
        "inputs": [item.get("path") for item in manifest.get("inputs", [])],
        "stage_inputs": {key: len(value) for key, value in manifest.get("stage_inputs", {}).items()},
        "public_files": manifest.get("public_files", []),
        "next_action": review_actions.get(stage, "run the current stage internally"),
    }


def print_json(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))


def select_project(project_id: str | None) -> dict:
    if project_id:
        return workflow.load_manifest(project_id)
    projects = workflow.list_projects()
    if not projects:
        raise RuntimeError("no projects")
    return projects[0]


def inbox_inputs() -> list[dict]:
    return [
        item for item in workflow.discover_files()
        if item.get("is_input") and item.get("name", "").lower() not in {"readme.md", "readme.txt"}
    ]


def command_status(args: argparse.Namespace) -> None:
    if args.project:
        print_json(compact_manifest(workflow.load_manifest(args.project)))
        return
    projects = workflow.list_projects()
    if projects:
        print_json({"projects": [compact_manifest(item) for item in projects]})
        return
    inputs = inbox_inputs()
    print_json({
        "projects": [],
        "inbox_inputs": [item["path"] for item in inputs],
        "next_action": "collect project name, duration, resolution, frame rate, and aspect ratio; offer chat storyboard drafting when no storyboard input is supplied",
    })


def command_create(args: argparse.Namespace) -> None:
    if not args.title or not args.duration or not args.resolution or not args.frame_rate or not args.aspect_ratio:
        raise RuntimeError("project name, duration, resolution, frame rate, and aspect ratio are required")
    files = args.file or [item["path"] for item in inbox_inputs()]
    title = args.title or Path(files[0]).stem
    manifest = workflow.create_project(title, files, {
        "purpose": args.purpose or "",
        "audience": args.audience or "",
        "duration": args.duration or "",
        "resolution": args.resolution or "",
        "frame_rate": args.frame_rate or "",
        "aspect_ratio": args.aspect_ratio or "",
        "platform": args.platform or "",
        "language": args.language or "",
        "tone": args.tone or "",
    })
    print_json(compact_manifest(manifest))


def command_task(args: argparse.Namespace) -> None:
    manifest = select_project(args.project)
    stage = args.stage or manifest.get("current_stage")
    if stage not in workflow.STAGES:
        raise RuntimeError(f"unknown stage: {stage}")
    root = workflow.project_dir(manifest["project_id"])
    task_dir = root / "codex_tasks"
    task_dir.mkdir(exist_ok=True)
    task = {
        "project_id": manifest["project_id"],
        "title": manifest["title"],
        "stage": stage,
        "status": manifest["stages"][stage]["status"],
        "inputs": manifest.get("inputs", []),
        "instruction_files": [
            "AGENTS.md",
            "instructions/core.md",
            f"instructions/stages/{workflow.STAGE_INSTRUCTION_FILES[stage]}",
        ],
        "expected_output": {
            "storyboard": "artifacts/*__s01__storyboard__v001.json",
            "prompts": "artifacts/*__s02__prompt-pack__v001.md",
            "image": "artifacts/final/thumbnail.png",
            "video": "artifacts/final/video.mp4",
            "remotion": "artifacts/final/infographic.mp4",
            "publish": "public/manifest.json",
        }[stage],
        "next_action": {
            "storyboard": "Show the storyboard form or draft and wait for the user's acceptance.",
            "image": "Use Codex image generation, display the result, and wait for the user's acceptance.",
            "video": "Use Higgsfield video generation, display the result, and wait for the user's acceptance.",
            "remotion": "Render a fast Remotion preview first, display it, and wait for the user's acceptance before full render.",
        }.get(stage, "Execute the current stage and report the exact output path."),
    }
    path = task_dir / f"{manifest['project_id']}__s{workflow.STAGE_NUMBERS[stage]:02d}__{stage}.json"
    workflow.write_json(path, task)
    print_json({"task": path.relative_to(root).as_posix(), "stage": stage, "status": task["status"], "next_action": task["next_action"]})


def command_attach(args: argparse.Namespace) -> None:
    manifest = workflow.attach_output(args.project, args.stage, args.file, args.phase)
    next_action = "ask the user to confirm the preview; full render comes next" if args.stage == "remotion" and args.phase == "preview" else "ask the user to confirm the current result in Codex"
    print_json({"project_id": manifest["project_id"], "stage": args.stage, "phase": args.phase, "status": manifest["stages"][args.stage]["status"], "next_action": next_action})


def command_run(args: argparse.Namespace) -> None:
    print_json(workflow.run_stage(args.project, args.stage))


def command_approve(args: argparse.Namespace) -> None:
    print_json(workflow.approve_stage(args.project, args.stage, args.note or ""))


def command_replace(args: argparse.Namespace) -> None:
    manifest = workflow.replace_stage_input(args.project, args.stage, args.file)
    print_json({"project_id": manifest["project_id"], "stage": args.stage, "status": manifest["stages"][args.stage]["status"], "next_action": "rerun the replaced stage"})


def main() -> int:
    parser = argparse.ArgumentParser(description="Compact Codex bridge for Tosun Workflow")
    subparsers = parser.add_subparsers(dest="command", required=True)
    status = subparsers.add_parser("status")
    status.add_argument("--project")
    status.set_defaults(handler=command_status)
    create = subparsers.add_parser("create")
    create.add_argument("--title", required=True)
    create.add_argument("--file", action="append")
    create.add_argument("--purpose")
    create.add_argument("--audience")
    create.add_argument("--duration", required=True)
    create.add_argument("--resolution", required=True)
    create.add_argument("--frame-rate", required=True)
    create.add_argument("--aspect-ratio", required=True)
    create.add_argument("--platform")
    create.add_argument("--language")
    create.add_argument("--tone")
    create.set_defaults(handler=command_create)
    task = subparsers.add_parser("task")
    task.add_argument("--project")
    task.add_argument("--stage")
    task.set_defaults(handler=command_task)
    attach = subparsers.add_parser("attach")
    attach.add_argument("--project", required=True)
    attach.add_argument("--stage", required=True, choices=["image", "video", "remotion"])
    attach.add_argument("--file", required=True)
    attach.add_argument("--phase", choices=["preview", "full"], default="full")
    attach.set_defaults(handler=command_attach)
    run = subparsers.add_parser("run")
    run.add_argument("--project", required=True)
    run.add_argument("--stage", required=True, choices=workflow.STAGES)
    run.set_defaults(handler=command_run)
    approve = subparsers.add_parser("approve")
    approve.add_argument("--project", required=True)
    approve.add_argument("--stage", required=True, choices=workflow.REVIEW_GATES)
    approve.add_argument("--note")
    approve.set_defaults(handler=command_approve)
    replace = subparsers.add_parser("replace")
    replace.add_argument("--project", required=True)
    replace.add_argument("--stage", required=True, choices=workflow.REVIEW_GATES)
    replace.add_argument("--file", required=True)
    replace.set_defaults(handler=command_replace)
    args = parser.parse_args()
    try:
        args.handler(args)
        return 0
    except Exception as error:
        print_json({"status": "failed", "error": str(error)})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

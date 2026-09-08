from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import tosun_workflow as workflow


class WorkflowGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        base = Path(self.temp.name)
        self.original_safe_path = workflow.safe_path
        self.workspace = base / "workspace"
        workflow.WORKSPACE = self.workspace
        workflow.INBOX = self.workspace / "inbox"
        workflow.PROJECTS = self.workspace / "projects"
        workflow.BACKUPS = self.workspace / "backups"
        workflow.EXPORTS = self.workspace / "exports"
        workflow.INSTRUCTIONS = base / "instructions"
        workflow.safe_path = lambda relative, base=workflow.WORKSPACE: self.original_safe_path(relative, base)
        workflow.ensure_layout()
        workflow.INSTRUCTIONS.mkdir(parents=True, exist_ok=True)
        self.storyboard = workflow.INBOX / "storyboard.md"
        self.storyboard.write_text("# Original storyboard\n", encoding="utf-8")
        manifest = workflow.create_project(
            "Guard test",
            ["inbox/storyboard.md"],
            {
                "duration": "10s",
                "resolution": "1920x1080",
                "frame_rate": "30",
                "aspect_ratio": "16:9",
            },
        )
        self.project_id = manifest["project_id"]

    def tearDown(self) -> None:
        workflow.safe_path = self.original_safe_path
        self.temp.cleanup()

    def test_attach_requires_stage_handoff(self) -> None:
        output = Path(self.temp.name) / "thumbnail.png"
        output.write_bytes(b"\x89PNG\r\n\x1a\nfake-image")
        with self.assertRaises(RuntimeError):
            workflow.attach_output(self.project_id, "image", str(output))

    def test_publish_ignores_unapproved_files(self) -> None:
        root = workflow.project_dir(self.project_id)
        final = root / "artifacts" / "final"
        final.mkdir(parents=True, exist_ok=True)
        (final / "thumbnail.png").write_bytes(b"unapproved")
        workflow.publish(workflow.load_manifest(self.project_id))
        public_manifest = json.loads((root / "public" / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(public_manifest["files"], [])
        self.assertFalse((root / "public" / "thumbnail.png").exists())

    def test_replacement_is_used_by_storyboard_analysis(self) -> None:
        replacement = Path(self.temp.name) / "replacement.md"
        replacement.write_text("# Replacement storyboard\n", encoding="utf-8")
        workflow.replace_stage_input(self.project_id, "storyboard", str(replacement))
        workflow.run_stage(self.project_id, "storyboard")
        root = workflow.project_dir(self.project_id)
        analysis = json.loads(next((root / "artifacts").glob("*__s01__storyboard__*.json")).read_text(encoding="utf-8"))
        self.assertEqual(analysis["inputs"][0]["name"], "replacement.md")

    def test_stage_failure_is_persisted(self) -> None:
        root = workflow.project_dir(self.project_id)
        (root / "input" / "source__storyboard.md").unlink()
        with self.assertRaises(FileNotFoundError):
            workflow.run_stage(self.project_id, "storyboard")
        state = workflow.load_manifest(self.project_id)["stages"]["storyboard"]
        self.assertEqual(state["status"], "failed")
        self.assertTrue(state["retryable"])
        self.assertTrue(state["error"])
        self.assertTrue(state["report"])


if __name__ == "__main__":
    unittest.main()

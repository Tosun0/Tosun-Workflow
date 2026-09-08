from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "plugins" / "tosun-workflow" / "skills"


class PluginSkillLayoutTests(unittest.TestCase):
    def test_expected_skill_layout(self) -> None:
        expected = {"master-tosun", "storyboard", "image", "video", "remotion"}
        actual = {path.parent.name for path in SKILLS.glob("*/SKILL.md")}
        self.assertEqual(expected, actual)

    def test_provider_routing_is_explicit(self) -> None:
        video = (SKILLS / "video" / "SKILL.md").read_text(encoding="utf-8")
        remotion = (SKILLS / "remotion" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("connected Higgsfield plugin", video)
        self.assertIn("installed Remotion plugin", remotion)
        self.assertIn("remotion:remotion-render", remotion)

    def test_master_owns_approval(self) -> None:
        master = (SKILLS / "master-tosun" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Never advance without explicit approval", master)
        self.assertIn("Remotion preview approval", master)


if __name__ == "__main__":
    unittest.main()

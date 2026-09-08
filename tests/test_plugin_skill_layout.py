from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "plugins" / "tosun-studio" / "skills"


class PluginSkillLayoutTests(unittest.TestCase):
    def test_expected_skill_layout(self) -> None:
        expected = {"00-master-tosun", "01-storyboard", "02-image", "03-video", "04-remotion"}
        actual = {path.parent.name for path in SKILLS.glob("*/SKILL.md")}
        self.assertEqual(expected, actual)

    def test_provider_routing_is_explicit(self) -> None:
        video = (SKILLS / "03-video" / "SKILL.md").read_text(encoding="utf-8")
        remotion = (SKILLS / "04-remotion" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("connected Higgsfield plugin", video)
        self.assertIn("installed Remotion plugin", remotion)
        self.assertIn("remotion:remotion-render", remotion)

    def test_master_owns_approval(self) -> None:
        master = (SKILLS / "00-master-tosun" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Never advance without explicit approval", master)
        self.assertIn("Remotion preview approval", master)


if __name__ == "__main__":
    unittest.main()

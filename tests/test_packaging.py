import importlib.util
import unittest

from foundry_workshop.contracts import read_json
from foundry_workshop.profiles import RuntimeProfile, packaged_profile

from . import ROOT, workspace


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PackagingTests(unittest.TestCase):
    def test_workflow_profiles_are_immutable_and_packaged_without_judge_data(self):
        with workspace() as root:
            builder = load_script("package_hosted")
            for pattern in ("sequential", "concurrent", "group-chat"):
                profile = RuntimeProfile(kind="workflow", pattern=pattern, protocol="invocations")
                destination = builder.build(root, profile)
                self.assertEqual(packaged_profile(destination), profile)
                manifest = read_json(destination / "package-manifest.json")
                self.assertEqual(manifest["runtime_profile"], profile.to_dict())
                self.assertIn("runtime-profile.json", manifest["files"])
                self.assertFalse((destination / "data/evaluation").exists())
                self.assertFalse(manifest["cloud_deployed"])

    def test_hosted_package_is_self_contained_and_excludes_evaluation(self):
        with workspace() as root:
            (root / ".env").write_text("SYNTHETIC_TEST_SECRET=must-not-be-packaged\n")
            builder = load_script("package_hosted")
            destination = builder.build(root)
            manifest = read_json(destination / "package-manifest.json")
            self.assertIn("main.py", manifest["files"])
            self.assertIn("foundry_workshop/agents.py", manifest["files"])
            self.assertIn("data/knowledge/policies.json", manifest["files"])
            self.assertFalse(manifest["cloud_deployed"])
            self.assertFalse((destination / ".env").exists())
            self.assertFalse((destination / "data/evaluation").exists())
            self.assertFalse((destination / "outputs").exists())
            ignore_patterns = set((destination / ".agentignore").read_text().splitlines())
            self.assertTrue(
                {".foundry/", "eval*.yaml", "eval*.yml", "data/evaluation/"}.issubset(
                    ignore_patterns
                )
            )
            self.assertNotIn(
                "microsoft-foundry-v1.5-labs[", (destination / "requirements.txt").read_text()
            )
            with self.assertRaises(ValueError):
                builder.build(root)

    def test_portal_export_has_six_labeled_text_documents(self):
        with workspace() as root:
            exporter = load_script("export_policy_docs")
            destination = exporter.export(root)
            files = list(destination.glob("*.txt"))
            self.assertEqual(len(files), 6)
            self.assertTrue(all("SYNTHETIC WORKSHOP POLICY" in path.read_text() for path in files))
            self.assertIn("150000", (destination / "TRAVEL-2026.txt").read_text())
            with self.assertRaises(FileExistsError):
                exporter.export(root)


if __name__ == "__main__":
    unittest.main()

import importlib.util
import io
import json
import shlex
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

from foundry_workshop.cli import main, parser
from foundry_workshop.contracts import load_cases, read_json
from foundry_workshop.profiles import RuntimeProfile, packaged_profile
from scripts.workshop import command_arguments

from . import ROOT, workspace


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PackagingTests(unittest.TestCase):
    def test_bilingual_intro_guides_serve_the_matching_workflow_profile(self):
        for language, relative in (
            ("ko", "docs/08-hosted.md"),
            ("en", "docs/en/08-hosted.md"),
        ):
            profiles = []
            for line in (ROOT / relative).read_text(encoding="utf-8").splitlines():
                if not line.startswith("python scripts/workshop.py "):
                    continue
                arguments = shlex.split(line)[2:]
                if "serve" not in arguments:
                    continue
                args = parser().parse_args(arguments)
                profiles.append(RuntimeProfile(**{
                    field: getattr(args, field) for field in RuntimeProfile.__dataclass_fields__
                }))
            with self.subTest(guide=relative):
                self.assertIn(RuntimeProfile(kind="workflow", language=language), profiles)

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


class GuideFlowTests(unittest.TestCase):
    def test_documented_first_offline_commands_work_without_azure_configuration(self):
        for language, edition in (("ko", ""), ("en", "en/")):
            commands = []
            for chapter in ("00-setup.md", "06-search-iq.md"):
                text = (ROOT / "docs" / edition / chapter).read_text(encoding="utf-8")
                for line in text.splitlines():
                    if not line.startswith("python scripts/workshop.py "):
                        continue
                    entry, arguments, _ = command_arguments(shlex.split(line)[2:])
                    if entry != "scripts/workshop.py":
                        continue
                    args = parser().parse_args(arguments)
                    if (
                        args.command == "doctor" and not args.cloud
                        or args.command == "retrieve" and args.provider == "local"
                    ):
                        commands.append((args, arguments))
            with (
                self.subTest(language=language),
                workspace() as root,
                patch("foundry_workshop.cli.cloud_command") as cloud,
            ):
                self.assertEqual(len(commands), 2)
                self.assertFalse((root / ".env").exists())
                self.assertFalse((root / ".selfstudy").exists())
                for args, arguments in commands:
                    stdout, stderr = io.StringIO(), io.StringIO()
                    with redirect_stdout(stdout), redirect_stderr(stderr):
                        status = main(root, arguments)
                    self.assertEqual(status, 0, stderr.getvalue())
                    result = json.loads(stdout.getvalue())
                    if args.command == "doctor":
                        self.assertEqual(result["language"], language)
                        self.assertEqual(
                            [result[key] for key in ("documents", "dev_cases", "holdout_cases")],
                            [6, 6, 4],
                        )
                        self.assertEqual(result["result"], "PASS")
                        self.assertFalse(result["azure_tested"])
                    else:
                        self.assertEqual(result["provider"], "local-keyword")
                        self.assertIn("TRAVEL-2026", result["source_ids"])
                        self.assertEqual(read_json(root / args.output), result)
                cloud.assert_not_called()

    def test_guardrail_questions_match_dev_cases_and_pin_independent_sessions(self):
        for language, edition in (("ko", ""), ("en", "en/")):
            cases = {case["case_id"]: case for case in load_cases(ROOT, "dev", language)}
            text = (ROOT / "docs" / edition / "13-governance.md").read_text(encoding="utf-8")
            invocations = [
                shlex.split(line)
                for line in text.splitlines()
                if line.startswith("azd ai agent invoke ")
            ]
            with self.subTest(language=language):
                self.assertEqual(
                    [command[-1] for command in invocations],
                    [cases["D01"]["question"], cases["D06"]["question"]],
                )
                for command in invocations:
                    for option in ("--cwd", "--version", "--new-session", "--new-conversation"):
                        self.assertIn(option, command)
                    self.assertNotIn("--local", command)
                for option in ("--cwd", "--version"):
                    self.assertEqual(
                        len({command[command.index(option) + 1] for command in invocations}), 1
                    )


if __name__ == "__main__":
    unittest.main()

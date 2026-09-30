import importlib.util
import io
import json
import re
import shlex
import tomllib
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch
from urllib.parse import unquote

from foundry_workshop.cli import main, parser
from foundry_workshop.contracts import load_cases, read_json
from foundry_workshop.experiments import offline_demo
from foundry_workshop.profiles import RuntimeProfile, packaged_profile
from scripts.check_workshop import headings
from scripts.workshop import command_arguments

from . import ROOT, workspace


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PackagingTests(unittest.TestCase):
    def test_workshop_release_metadata_is_consistent(self):
        workshop_version = read_json(ROOT / "curriculum.json")["version"]
        project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
        self.assertEqual(workshop_version, "1.3")
        self.assertEqual(project["name"], f"microsoft-foundry-v{workshop_version}-labs")
        self.assertEqual(project["version"], f"{workshop_version}.0")
        self.assertIn(f"Microsoft Foundry v{workshop_version} workshop.", parser().description)
        for extra, dependency in (("agents", "cloud"), ("hosted", "agents")):
            self.assertIn(
                f"{project['name']}[{dependency}]", project["optional-dependencies"][extra]
            )

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
                "microsoft-foundry-v1.3-labs[", (destination / "requirements.txt").read_text()
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
    @staticmethod
    def workshop_commands(relative):
        for line in (ROOT / relative).read_text(encoding="utf-8").splitlines():
            if not line.startswith("python scripts/workshop.py "):
                continue
            entry, arguments, _ = command_arguments(shlex.split(line)[2:])
            if entry == "scripts/workshop.py":
                yield parser().parse_args(arguments), arguments

    def test_bilingual_readmes_introduce_the_ignite_predecessor(self):
        for relative, date in (
            ("README.ko.md", "2025년 11월"),
            ("README.md", "November 2025"),
        ):
            introduction = (ROOT / relative).read_text(encoding="utf-8").split("## ", 1)[0]
            with self.subTest(readme=relative):
                self.assertIn(
                    "https://github.com/junwoojeong100/microsoft-foundry-labs)",
                    introduction,
                )
                self.assertIn("Microsoft Ignite 2025", introduction)
                self.assertIn(date, introduction)

    def test_documented_first_offline_commands_work_without_azure_configuration(self):
        for language, edition in (("ko", ""), ("en", "en/")):
            commands = []
            for chapter in ("00-setup.md", "06-search-iq.md"):
                for args, arguments in self.workshop_commands(f"docs/{edition}{chapter}"):
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

    def test_documented_comparison_reads_saved_results_and_reports_quality_failures(self):
        for language, edition in (("ko", ""), ("en", "en/")):
            relative = f"docs/{edition}07-evaluation.md"
            guide = (ROOT / relative).read_text(encoding="utf-8")
            commands = list(self.workshop_commands(relative))
            runs = {
                args.label: args
                for args, _ in commands
                if args.command == "collect" and args.api == "project-responses"
            }
            with (
                self.subTest(language=language),
                workspace() as root,
                patch("foundry_workshop.cli.cloud_command") as cloud,
            ):
                self.assertEqual(len(runs), 2)
                for args in runs.values():
                    offline_demo(root, args.label, args.prompt, language=language)
                evaluated = []
                compared = []
                for args, arguments in commands:
                    if args.command == "evaluate" and args.label in runs:
                        evaluated.append(args.label)
                    elif (
                        args.command == "compare"
                        and args.baseline in runs
                        and args.candidate in runs
                    ):
                        compared.append(args.candidate)
                    else:
                        continue
                    stdout, stderr = io.StringIO(), io.StringIO()
                    with redirect_stdout(stdout), redirect_stderr(stderr):
                        status = main(root, arguments)
                    result = json.loads(stdout.getvalue())
                    self.assertNotEqual(result["mode"], "live")
                    if args.command == "evaluate":
                        self.assertEqual(result["total"], 6)
                        self.assertEqual(result["errors"], 0)
                        self.assertEqual(len(result["checks"]), 6)
                        expected_pass = runs[args.label].prompt == "v2"
                        self.assertEqual(result["business_gate_passed"], expected_pass)
                        self.assertEqual(status, 0 if expected_pass else 1)
                        output = root / "outputs" / args.label / "business-evaluation.json"
                        self.assertIn(f"outputs/{args.label}/", guide)
                        self.assertIn(output.name, guide)
                    else:
                        self.assertEqual(status, 0, stderr.getvalue())
                        self.assertFalse(result["baseline_metrics"]["business_gate_passed"])
                        self.assertTrue(result["candidate_metrics"]["business_gate_passed"])
                        output = (
                            root / "outputs" / args.candidate
                            / f"comparison-vs-{args.baseline}.json"
                        )
                        self.assertIn(output.relative_to(root).as_posix(), guide)
                    self.assertEqual(read_json(output), result)
                self.assertEqual(set(evaluated), set(runs))
                self.assertEqual(len(compared), 1)
                cloud.assert_not_called()

    def test_documented_final_targets_match_their_dev_collection_profiles(self):
        for language, edition, target_count in (("ko", "", 2), ("en", "en/", 3)):
            dev_runs = {}
            for chapter in ("07-evaluation.md", "12-improvement.md"):
                for args, _ in self.workshop_commands(f"docs/{edition}{chapter}"):
                    if args.command == "collect" or (
                        args.command == "benchmark" and args.benchmark_action == "collect"
                    ):
                        self.assertEqual(args.split, "dev")
                        self.assertFalse(args.unlock_holdout)
                        dev_runs[args.command, args.label] = args
            final_runs = [
                args
                for args, _ in self.workshop_commands(f"docs/{edition}15-capstone-cleanup.md")
                if args.command == "collect"
                or args.command == "benchmark" and args.benchmark_action == "collect"
            ]
            with self.subTest(language=language):
                self.assertEqual(len(final_runs), target_count)
                for args in final_runs:
                    candidate = dev_runs[args.command, args.candidate]
                    self.assertEqual(args.split, "holdout")
                    self.assertTrue(args.unlock_holdout)
                    self.assertNotIn((args.command, args.label), dev_runs)
                    self.assertEqual(args.language, language)
                    fields = ("language", "prompt", "retrieval", "api")
                    if args.command == "benchmark":
                        fields += ("kind", "pattern", "protocol", "concurrency")
                    for field in fields:
                        self.assertEqual(
                            getattr(args, field), getattr(candidate, field),
                            f"{args.label}: mismatched {field}",
                        )

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


class GuideReadabilityTests(unittest.TestCase):
    @staticmethod
    def chapters():
        steps = read_json(ROOT / "curriculum.json")["steps"]
        for language in ("ko", "en"):
            paths = [
                ROOT / step["file"]
                if language == "ko"
                else ROOT / "docs/en" / step["file"].rsplit("/", 1)[-1]
                for step in steps
            ]
            for index, path in enumerate(paths):
                yield language, paths, index, path

    def test_bilingual_chapters_have_maps_and_matching_navigation(self):
        for language, paths, index, path in self.chapters():
            text = path.read_text(encoding="utf-8")
            introduction = text.split("\n## ", 1)[0]
            home = (
                "../README.ko.md#진행-순서"
                if language == "ko"
                else "../../README.md#curriculum"
            )
            translation = f"en/{path.name}" if language == "ko" else f"../{path.name}"
            markers = (
                ("**완료 목표:**", "**시작 조건:**", "**실행 위치:**", "**진행 지도**")
                if language == "ko"
                else ("**Outcome:**", "**Prerequisites:**", "**Where you work:**", "**Chapter map**")
            )
            with self.subTest(guide=path.relative_to(ROOT)):
                for marker in markers:
                    self.assertIn(marker, introduction)
                for target in (home, translation, "checkpoints.md"):
                    self.assertIn(f"]({target})", introduction)
                chapter_map = introduction.split(markers[-1], 1)[1]
                anchors = re.findall(r"\]\(#([^)\n]+)\)", chapter_map)
                self.assertGreaterEqual(len(anchors), 4)
                self.assertTrue({unquote(anchor) for anchor in anchors} <= headings(path))
                self.assertEqual(introduction.count('<a id="chapter-map"></a>'), 1)
                self.assertIn("\n---\n", text)
                footer = text.rsplit("\n---\n", 1)[1]
                self.assertIn(f"]({home})", footer)
                self.assertIn("](#chapter-map)", footer)
                if index:
                    self.assertIn(f"]({paths[index - 1].name})", footer)
                if index + 1 < len(paths):
                    self.assertIn(f"]({paths[index + 1].name})", footer)

    def test_executable_blocks_contain_one_command_for_safe_copying(self):
        paths = [path for _, _, _, path in self.chapters()]
        paths.extend(
            ROOT / relative
            for relative in (
                "README.md", "README.ko.md", "docs/checkpoints.md", "docs/en/checkpoints.md",
            )
        )
        for path in paths:
            text = path.read_text(encoding="utf-8")
            blocks = re.findall(r"^```(?:bash|powershell)\n(.*?)\n```", text, re.MULTILINE | re.DOTALL)
            with self.subTest(guide=path.relative_to(ROOT)):
                self.assertTrue(blocks)
                for block in blocks:
                    commands = [line for line in block.splitlines() if line.strip()]
                    self.assertEqual(
                        len(commands), 1,
                        f"Keep independently executed commands in separate copyable blocks: {block}",
                    )

    def test_troubleshooting_groups_complete_answers_without_wide_tables(self):
        categories = {
            "environment", "identity", "models", "retrieval", "tools",
            "evaluation", "managed-safety", "observability", "state-schedules",
        }
        for language, relative in (
            ("ko", "docs/troubleshooting.md"),
            ("en", "docs/en/troubleshooting.md"),
        ):
            text = (ROOT / relative).read_text(encoding="utf-8")
            answers = re.findall(
                r"<details>\s*<summary>(.*?)</summary>\s*(.*?)\s*</details>",
                text, re.DOTALL,
            )
            labels = (
                ("**먼저 할 일:**", "**먼저 확인:**", "**다음 행동:**")
                if language == "ko"
                else ("**First action:**", "**Check first:**", "**Next action:**")
            )
            with self.subTest(guide=relative):
                for anchor in categories:
                    self.assertEqual(text.count(f'<a id="{anchor}"></a>'), 1)
                    self.assertIn(f"](#{anchor})", text)
                self.assertNotRegex(text, r"(?m)^\|")
                self.assertGreaterEqual(len(answers), 75)
                self.assertEqual(len(answers), text.count("<details>"))
                self.assertEqual(len(answers), text.count("</details>"))
                for summary, body in answers:
                    self.assertTrue(summary.strip())
                    self.assertNotIn("`", summary, "Use HTML code tags inside disclosure summaries.")
                    if labels[0] not in body:
                        self.assertIn(labels[1], body)
                        self.assertIn(labels[2], body)

    def test_default_steps_and_completion_remain_visible_and_reachable(self):
        for language, _, index, path in self.chapters():
            text = path.read_text(encoding="utf-8")
            introduction = text.split("\n## ", 1)[0]
            visible_headings = []
            details = 0
            fenced = False
            with self.subTest(guide=path.relative_to(ROOT)):
                for line in text.splitlines():
                    if line.startswith("```"):
                        fenced = not fenced
                    elif not fenced:
                        if line == "<details>":
                            details += 1
                        elif line == "</details>":
                            details -= 1
                            self.assertGreaterEqual(details, 0)
                        elif not details and line.startswith("## "):
                            visible_headings.append(line[3:])
                self.assertFalse(fenced)
                self.assertEqual(details, 0)
                self.assertEqual(text.count("<details>"), text.count("<summary>"))
                self.assertEqual(text.count("<summary>"), text.count("</summary>"))
                for title in visible_headings:
                    number = re.match(r"(\d+)\. ", title)
                    if number:
                        self.assertRegex(
                            introduction,
                            rf"\]\(#{number.group(1)}-[^)\n]+\)",
                            f"Default step missing from chapter map: {title}",
                        )
                completion = (
                    ("7. 최종 확인" if language == "ko" else "7. Final checklist")
                    if index == 15
                    else ("완료 확인" if language == "ko" else "Completion check")
                )
                self.assertIn(completion, visible_headings)
                checklist = text.split(f"\n## {completion}\n", 1)[1].split("\n---\n", 1)[0]
                self.assertGreaterEqual(len(re.findall(r"^- \[ \] ", checklist, re.MULTILINE)), 3)

    def test_korean_emphasis_avoids_punctuation_before_particles(self):
        paths = [path for language, _, _, path in self.chapters() if language == "ko"]
        paths.extend(
            ROOT / relative
            for relative in ("README.ko.md", "docs/checkpoints.md", "docs/troubleshooting.md")
        )
        for path in paths:
            fenced = False
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if line.startswith("```"):
                    fenced = not fenced
                elif not fenced:
                    with self.subTest(guide=path.relative_to(ROOT), line=number):
                        self.assertNotRegex(
                            line, r"[`)\]↑]\*\*[가-힣]",
                            "Use code/link styling alone, or end bold before punctuation.",
                        )


if __name__ == "__main__":
    unittest.main()

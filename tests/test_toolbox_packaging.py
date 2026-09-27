import os
import unittest
from unittest.mock import patch

from foundry_workshop.contracts import read_json
from foundry_workshop.toolbox import require_synthetic_index

from . import workspace
from .test_packaging import load_script
from .test_toolbox import ENVIRONMENT, seed_ledger, settings

PACKAGE = load_script("package_toolbox")


class ToolboxPackageTests(unittest.TestCase):
    def test_package_pins_the_toolbox_and_contains_no_evaluation_answers(self):
        with workspace() as root, patch.dict(os.environ, ENVIRONMENT, clear=True):
            seed_ledger(root)
            destination = PACKAGE.build(root, settings(), "2")
            profile = read_json(destination / "toolbox-profile.json")
            self.assertEqual(profile["toolbox_version"], "2")
            self.assertEqual(profile["runtime"]["toolbox_name"], "lab-unit-tools-en")
            self.assertEqual(len(profile["questions"]), 6)
            self.assertFalse((destination / "data/evaluation").exists())
            self.assertFalse((destination / ".env").exists())
            self.assertFalse((destination / "outputs").exists())
            self.assertFalse(read_json(destination / "package-manifest.json")["cloud_deployed"])
            require_synthetic_index(destination, settings(), packaged_source=profile["source"])
            with self.assertRaises(FileExistsError):
                PACKAGE.build(root, settings(), "2")

    def test_remote_source_must_be_explicit_and_cannot_fall_back_after_mismatch(self):
        with workspace() as root, patch.dict(os.environ, ENVIRONMENT, clear=True):
            seed_ledger(root)
            destination = PACKAGE.build(root, settings(), "2")
            profile = read_json(destination / "toolbox-profile.json")
            with self.assertRaisesRegex(ValueError, "seed-search"):
                require_synthetic_index(destination, settings())
            profile["source"]["index"] = "another-index"
            with self.assertRaisesRegex(ValueError, "packaged synthetic source"):
                require_synthetic_index(destination, settings(), packaged_source=profile["source"])

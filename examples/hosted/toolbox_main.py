from pathlib import Path

from foundry_workshop.contracts import read_json
from foundry_workshop.settings import Settings, require_env
from foundry_workshop.toolbox import name_for
from foundry_workshop.toolbox_host import serve


def main():
    root = Path(__file__).resolve().parent
    profile = read_json(root / "toolbox-profile.json")
    if profile.get("kind") != "synthetic-toolbox-host" or profile.get("schema_version") != 1:
        raise ValueError("Use a package produced by scripts/package_toolbox.py.")
    settings = Settings.from_env(language=profile["language"])
    actual = {
        "project_endpoint": settings.project_endpoint,
        "deployment": settings.deployment,
        "toolbox_name": name_for(settings),
        "search_connection": require_env("TOOLBOX_SEARCH_CONNECTION_NAME"),
    }
    if profile["runtime"] != actual:
        raise ValueError(
            "The runtime project/model/Toolbox/connection differs from the pinned package."
        )
    serve(
        root,
        settings,
        profile["toolbox_version"],
        with_skill=profile["with_skill"],
        packaged_source=profile["source"],
        questions=profile["questions"],
        evidence_root=Path.home() / "workshop-evidence/toolbox-runs",
    )


if __name__ == "__main__":
    main()

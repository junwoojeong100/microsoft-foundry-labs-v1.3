from pathlib import Path

from foundry_workshop.agents import serve
from foundry_workshop.profiles import packaged_profile
from foundry_workshop.settings import Settings

if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    profile = packaged_profile(root)
    serve(Settings.from_env(language=profile.language), root, profile)

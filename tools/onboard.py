import argparse
import re
from pathlib import Path

import yaml


ROOT_DIR = Path(__file__).resolve().parents[1]
APPS_DIR = ROOT_DIR / "apps"


def validate_name(name):
    pattern = r"[a-z][a-z0-9-]{0,51}[a-z0-9]|[a-z]"

    if not re.fullmatch(pattern, name):
        raise ValueError(
            "Application name must be 1-53 characters, "
            "start with a lowercase letter, and contain "
            "only lowercase letters, numbers and hyphens."
        )


def validate_config(args):
    validate_name(args.name)

    if not 1 <= args.port <= 65535:
        raise ValueError("Port must be between 1 and 65535.")

    if not 1 <= args.replicas <= 10:
        raise ValueError("Replicas must be between 1 and 10.")

    if not args.image.strip() or not args.tag.strip():
        raise ValueError("Image and tag cannot be empty.")

    if args.tag == "latest":
        raise ValueError("The latest image tag is not allowed.")

    if not args.health_path.startswith("/"):
        raise ValueError("Health path must start with /.")


def generate_values(args):
    return {
        "replicaCount": args.replicas,
        "image": {
            "repository": args.image,
            "tag": args.tag,
        },
        "containerPort": args.port,
        "probes": {
            "readiness": {
                "enabled": True,
                "path": args.health_path,
            },
            "liveness": {
                "enabled": True,
                "path": args.health_path,
            },
        },
    }


def onboard(args):
    validate_config(args)

    app_dir = APPS_DIR / args.name
    values_file = app_dir / "values.yaml"

    values = generate_values(args)

    if args.dry_run:
        print(yaml.safe_dump(values, sort_keys=False))
        return

    app_dir.mkdir(parents=True, exist_ok=True)

    with values_file.open("x") as file:
        yaml.safe_dump(values, file, sort_keys=False)

    print(f"Application configuration created: {values_file}")
    print("Review, commit and push to trigger deployment.")


def main():
    parser = argparse.ArgumentParser(
        description="Developer platform onboarding CLI"
    )

    parser.add_argument("--name", required=True)
    parser.add_argument("--image", required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--replicas", type=int, default=1)
    parser.add_argument("--health-path", default="/")
    parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()

    try:
        onboard(args)
    except (ValueError, OSError) as error:
        parser.exit(1, f"Error: {error}\n")


if __name__ == "__main__":
    main()
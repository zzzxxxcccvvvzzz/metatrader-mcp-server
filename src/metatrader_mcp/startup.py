import json
from importlib import metadata
from pathlib import Path
from typing import Optional

import click

PACKAGE_NAME = "metatrader-mcp-server"


def _is_local_source_tree(module_file: Path) -> bool:
    try:
        repo_root = module_file.resolve().parents[2]
    except IndexError:
        return False
    return (repo_root / "pyproject.toml").exists() and (repo_root / "src").exists()


def detect_install_source() -> tuple[str, Optional[str]]:
    module_file = Path(__file__).resolve()

    try:
        dist = metadata.distribution(PACKAGE_NAME)
    except metadata.PackageNotFoundError:
        if _is_local_source_tree(module_file):
            return "local-source", str(module_file.parents[2])
        return "unknown", None

    try:
        direct_url_path = Path(dist.locate_file("direct_url.json"))
    except Exception:
        direct_url_path = None

    if direct_url_path and direct_url_path.exists():
        try:
            direct_url = json.loads(direct_url_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            direct_url = {}

        source_url = direct_url.get("url", "")
        if source_url.startswith("file://"):
            local_hint = source_url.removeprefix("file://").replace("/", "\\")
            editable = bool(direct_url.get("dir_info", {}).get("editable"))
            if editable:
                return "local-editable", local_hint
            return "local-build", local_hint

    if _is_local_source_tree(module_file):
        return "local-source", str(module_file.parents[2])

    return "installed-package", None


def get_startup_banner(service_name: str, version: str, command_name: str) -> str:
    source_kind, source_hint = detect_install_source()
    lines = [
        f"[{service_name}] v{version}",
        f"Command: {command_name}",
    ]

    if source_kind == "local-editable":
        lines.extend(
            [
                "Easter Egg: LOCAL EDITABLE BUILD DETECTED",
                "This command is running from your local source, not a package downloaded from pip.",
            ]
        )
    elif source_kind in {"local-build", "local-source"}:
        lines.extend(
            [
                "Easter Egg: LOCAL BUILD DETECTED",
                "This command is running from your own package, not a package downloaded from pip.",
            ]
        )
    else:
        lines.append("Install Source: installed package")

    if source_hint:
        lines.append(f"Source Path: {source_hint}")

    return "\n".join(lines)


def echo_startup_banner(service_name: str, version: str, command_name: str) -> None:
    click.echo(get_startup_banner(service_name, version, command_name))
    click.echo()

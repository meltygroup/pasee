"""Entry point for console script.
"""

import argparse
import os
import sys
from typing import Optional, Dict

from aiohttp import web
import pytoml as toml

try:
    import sentry_sdk
    from sentry_sdk.integrations.aiohttp import AioHttpIntegration  # pragma: no cover
except ImportError:
    sentry_sdk = None

import pasee
from pasee import MissingSettings
from pasee.pasee import identification_app


def pasee_arg_parser() -> argparse.ArgumentParser:
    """Parses command line arguments.
    """
    parser = argparse.ArgumentParser(
        prog="pasee",
        description="Pasee Identity Manager",
        epilog="All options, if given, take precedence over settings file.",
    )
    parser.add_argument("--settings-file")
    parser.add_argument(
        "--settings",
        help="Compatibility option for --settings-file",
        default="settings.toml",
    )
    parser.add_argument("--host", help="Hostname to bind to.")
    parser.add_argument("--port", help="Port to bind to.")
    return parser


def load_conf(
    settings_path: Optional[str] = None, host: str = None, port: int = None,
) -> Dict:
    """Search for a settings.toml file and load it.
    """
    candidates: tuple
    if settings_path:
        candidates = (
            settings_path,
            os.path.join(os.getcwd(), settings_path),
            os.path.join(os.getcwd(), "settings.toml"),
            os.path.expanduser("~/settings.toml"),
            os.path.expanduser(os.path.join("~/", settings_path)),
            "/etc/pasee/settings.toml",
            os.path.join("/etc/pasee/", settings_path),
        )
    else:
        candidates = (
            os.path.join(os.getcwd(), "settings.toml"),
            os.path.expanduser("~/settings.toml"),
            "/etc/pasee/settings.toml",
        )
    settings = None
    for candidate in candidates:
        if os.path.exists(candidate):
            with open(candidate) as candidate_file:
                settings = toml.load(candidate_file)
                break
    if not settings:
        raise MissingSettings(
            f"No settings files found, tried: {', '.join(set(candidates))}"
        )

    if host:
        settings["host"] = host
    if "host" not in settings:
        settings["host"] = "127.0.0.1"
    if port:
        settings["port"] = port
    if "port" not in settings:
        settings["port"] = 8140
    for mandatory_setting in {"private_key", "public_key", "identity_providers"}:
        if mandatory_setting not in settings:
            raise MissingSettings(f"No {mandatory_setting} in settings, see README.md")
    settings["idps"] = {idp["name"]: idp for idp in settings["identity_providers"]}
    return settings


def main():  # pragma: no cover
    """Command line entry point.
    """
    parser = pasee_arg_parser()
    args = parser.parse_args()
    try:
        settings = load_conf(args.settings_file or args.settings, args.host, args.port)
    except pasee.MissingSettings as err:
        print(err, file=sys.stderr)
        parser.print_help()
        sys.exit(1)
    if sentry_sdk:
        sentry_sdk.init(settings.get("SENTRY_DSN"), integrations=[AioHttpIntegration()])
    app = identification_app(settings)
    web.run_app(app, host=app["settings"]["host"], port=app["settings"]["port"])


if __name__ == "__main__":
    main()

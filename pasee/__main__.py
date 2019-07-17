"""Entry point for console script.
"""

import argparse
import sys

from aiohttp import web

try:
    import sentry_sdk
except ImportError:
    sentry_sdk = None

import pasee
from pasee.pasee import identification_app


def pasee_arg_parser() -> argparse.ArgumentParser:
    """Parses command line arguments.
    """
    parser = argparse.ArgumentParser(
        prog="pasee",
        description="Pasee Identity Manager",
        epilog="All options, if given, take precedence over settings file.",
    )
    parser.add_argument("--settings-file", default="settings.toml")
    parser.add_argument("--host", help="Hostname to bind to.")
    parser.add_argument("--port", help="Port to bind to.")
    return parser


def main():  # pragma: no cover
    """Command line entry point.
    """
    if sentry_sdk:
        sentry_sdk.init()

    parser = pasee_arg_parser()
    try:
        app = identification_app(**vars(parser.parse_args()))
    except pasee.MissingSettings as err:
        print(err, file=sys.stderr)
        parser.print_help()
        exit(1)
    web.run_app(app, host=app.settings["host"], port=app.settings["port"])


if __name__ == "__main__":
    main()

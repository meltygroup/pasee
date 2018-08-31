"""Tests for the app
"""


import sys
from unittest.mock import patch

import pasee.__main__ as main


def test_parse_args():
    """Test the argument parsing
    """
    with patch.object(sys, "argv", ["dummy"]):
        args = main.pasee_arg_parser().parse_args()
        assert args.settings_file == "settings.toml"

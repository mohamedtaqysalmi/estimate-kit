import re

import estimate_kit


def test_version_is_semver_like() -> None:
    assert re.fullmatch(r"\d+\.\d+\.\d+", estimate_kit.__version__)

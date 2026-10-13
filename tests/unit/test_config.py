# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Where settings come from, and in what order they win."""

from __future__ import annotations

from pathlib import Path

import pytest

from benchproofer.config import CONFIG_FILENAME, Settings, load_settings
from benchproofer.errors import ConfigError


def write_config(directory: Path, body: str) -> Path:
    path = directory / CONFIG_FILENAME
    path.write_text(body, encoding="utf-8")
    return path


def test_defaults_are_offline_free_and_model_free() -> None:
    """An installation with no configuration still has a usable, honest default."""
    defaults = Settings()

    assert defaults.provider == "null"
    assert defaults.bundle_root == Path("bundles")
    assert not defaults.offline


def test_a_config_file_is_read_from_the_working_directory(tmp_path: Path) -> None:
    write_config(tmp_path, '[benchproofer]\nprovider = "replay"\nconcurrency = 8\n')

    resolved = load_settings(base=tmp_path)

    assert resolved.provider == "replay"
    assert resolved.concurrency == 8


def test_a_config_file_without_the_table_header_is_read_too(tmp_path: Path) -> None:
    write_config(tmp_path, 'provider = "replay"\n')

    assert load_settings(base=tmp_path).provider == "replay"


def test_the_environment_beats_the_file_and_an_option_beats_both(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_config(tmp_path, '[benchproofer]\nmodel = "from-file"\n')
    monkeypatch.setenv("BENCHPROOFER_MODEL", "from-environment")

    assert load_settings(base=tmp_path).model == "from-environment"
    assert load_settings({"model": "from-option"}, base=tmp_path).model == "from-option"


def test_an_unset_option_does_not_override_anything(tmp_path: Path) -> None:
    """CLI options default to None so that not passing one is not a choice."""
    write_config(tmp_path, '[benchproofer]\nmodel = "from-file"\n')

    assert load_settings({"model": None}, base=tmp_path).model == "from-file"


def test_relative_paths_are_anchored_where_the_command_was_run(tmp_path: Path) -> None:
    write_config(tmp_path, '[benchproofer]\nbundle_root = "corpus"\n')

    resolved = load_settings(base=tmp_path)

    assert resolved.bundle_root == (tmp_path / "corpus").resolve()
    assert resolved.cache_dir.is_absolute()
    assert resolved.toolchain_dir == (tmp_path / ".toolchains").resolve()


def test_an_absolute_path_is_left_alone(tmp_path: Path) -> None:
    elsewhere = tmp_path / "elsewhere"

    resolved = load_settings({"bundle_root": elsewhere}, base=tmp_path)

    assert resolved.bundle_root == elsewhere


def test_a_broken_config_file_names_itself(tmp_path: Path) -> None:
    write_config(tmp_path, "this is not toml\n")

    with pytest.raises(ConfigError, match=CONFIG_FILENAME):
        load_settings(base=tmp_path)


def test_a_config_file_whose_table_is_not_a_table_is_refused(tmp_path: Path) -> None:
    write_config(tmp_path, "benchproofer = 3\n")

    with pytest.raises(ConfigError, match="must be a table"):
        load_settings(base=tmp_path)


def test_settings_are_frozen_and_copies_are_explicit() -> None:
    original = Settings()

    tuned = original.model_copy(update={"offline": True})

    assert not original.offline
    assert tuned.offline

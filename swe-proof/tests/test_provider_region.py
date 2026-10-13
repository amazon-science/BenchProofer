# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The region a provider talks to is configuration, not a constant.

Which region hosts a given model is a property of the account, so the presets
carry a default rather than a hard-coded value. Getting this wrong is invisible
until the first request, and then every request fails identically with an access
error that names the MODEL -- so the failure reads as "we are not entitled to
this model" when the real cause is "not in that region". These pin the override
order and the empty-string case.
"""
from __future__ import annotations

from swebench_unified.eval.providers import (
    MODEL_PRESETS, resolve_region,
)

_VARS = ("SBU_BEDROCK_REGION", "AWS_REGION", "AWS_DEFAULT_REGION")


def _clear(monkeypatch):
    for name in _VARS:
        monkeypatch.delenv(name, raising=False)


def test_the_presets_default_survives_when_nothing_is_set(monkeypatch):
    _clear(monkeypatch)
    assert resolve_region("us-west-2") == "us-west-2"
    assert resolve_region("eu-central-1") == "eu-central-1"


def test_the_projects_own_variable_wins(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("SBU_BEDROCK_REGION", "eu-west-1")
    monkeypatch.setenv("AWS_REGION", "ap-south-1")
    assert resolve_region("us-west-2") == "eu-west-1"


def test_the_standard_aws_variables_are_honored(monkeypatch):
    """These providers pass region_name explicitly, which beats the environment
    boto3 would otherwise read -- so ignoring them would silently override a
    setting the rest of the caller's toolchain already obeys."""
    _clear(monkeypatch)
    monkeypatch.setenv("AWS_REGION", "ap-south-1")
    assert resolve_region("us-west-2") == "ap-south-1"
    monkeypatch.delenv("AWS_REGION")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "sa-east-1")
    assert resolve_region("us-west-2") == "sa-east-1"


def test_aws_region_beats_the_default_region(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("AWS_REGION", "ap-south-1")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "sa-east-1")
    assert resolve_region("us-west-2") == "ap-south-1"


def test_an_empty_value_means_unset(monkeypatch):
    """A profile that exports the variable empty is the common shape, and taking
    it literally builds a client with region_name="" that fails at the first
    call rather than at configuration time."""
    _clear(monkeypatch)
    monkeypatch.setenv("SBU_BEDROCK_REGION", "")
    monkeypatch.setenv("AWS_REGION", "   ")
    assert resolve_region("us-west-2") == "us-west-2"


def test_a_whitespace_padded_value_is_used_trimmed(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("SBU_BEDROCK_REGION", " eu-west-1\n")
    assert resolve_region("us-west-2") == "eu-west-1"


def test_every_preset_still_carries_its_own_region_default():
    """The defaults are per model because model availability is per region: a
    single shared default would send one preset to a region its model is not in.
    An override applies to all of them, which is the caller's choice to make."""
    for key, spec in MODEL_PRESETS.items():
        if spec.get("provider") in ("bedrock", "openai_responses"):
            assert spec.get("region"), f"{key} has no region default"


def test_bedrock_anthropic_presets_carry_the_inference_profile_prefix():
    """Bedrock serves these models through a cross-region inference profile, so a
    bare `anthropic.claude-...` id is not callable: the request fails with an
    error that names the model, which reads as a missing entitlement."""
    for key, spec in MODEL_PRESETS.items():
        if spec.get("provider") == "bedrock" and "anthropic" in spec["model_id"]:
            assert spec["model_id"].startswith("us."), f"{key} lacks the us. prefix"


def test_the_judge_keys_a_run_can_record_stay_available():
    """A run and an audit record their judge by preset key, so dropping a key
    makes every record naming it unreproducible."""
    for key in ("opus-5", "opus-4.8"):
        assert key in MODEL_PRESETS

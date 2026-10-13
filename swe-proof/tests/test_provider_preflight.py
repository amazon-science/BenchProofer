# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""A driver with no provider configured must fail loudly, not stall the host.

The agent CLI reports a missing provider exactly as it reports lapsed
credentials: "Not logged in". The response to lapsed credentials is a HOST-WIDE
backoff -- one flag file whose mtime every driver waits out -- and that is right
for an outage and catastrophic for a misconfiguration, because the misconfigured
driver never recovers, so it re-stamps the flag every quiet period and no launch
anywhere on the host ever runs. A supervisor launched by a scheduler inherits
none of a shell's provider routing, so it re-stamps the flag indefinitely and
every cell it audits comes back with all its audit roles inconclusive -- which
reads downstream as a wall of spec defects.

So the two cases are separated before the wait: configuration is checked in the
process that has the problem, and reported to its caller.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from swebench_unified.agent import provider_preflight

ROOT = Path(__file__).resolve().parents[1]

# `AgentAuthError` and `run_agent_step` are deliberately NOT imported here. They
# are reached through the module object inside the test that needs them, so the
# patch and the call can never end up on different copies of the module.


def _env(**kw) -> dict:
    """An environment with no provider route at all, plus overrides."""
    base = {"HOME": "/nonexistent-home", "PATH": "/usr/bin"}
    base.update(kw)
    return base


def test_a_bare_environment_is_reported_as_unconfigured():
    why = provider_preflight(_env())
    assert why and "no provider is configured" in why


ROUTES = [
    ("CLAUDE_CODE_USE_BEDROCK", "1"),
    ("CLAUDE_CODE_USE_VERTEX", "1"),
    ("ANTHROPIC_API_KEY", "sk-test"),
    ("ANTHROPIC_AUTH_TOKEN", "tok"),
    ("CLAUDE_CODE_OAUTH_TOKEN", "tok"),
]


@pytest.mark.parametrize("var,val", ROUTES)
def test_each_supported_route_counts_as_configured(var, val):
    assert provider_preflight(_env(**{var: val})) == ""


@pytest.mark.parametrize("var,val", ROUTES)
def test_the_refusal_names_every_route_it_accepts(var, val):
    """The message is the whole remediation an operator gets, and it left
    CLAUDE_CODE_OAUTH_TOKEN out while the check above accepted it: someone
    holding exactly that route was told none was configured."""
    assert var in provider_preflight(_env())


@pytest.mark.parametrize("val", ["", "0", "false", "  "])
def test_a_switched_off_flag_is_not_a_route(val):
    """`CLAUDE_CODE_USE_BEDROCK=0` is how a caller asks for the other route, so
    reading it as configured would send the launch at a provider it disabled."""
    assert provider_preflight(_env(CLAUDE_CODE_USE_BEDROCK=val)) != ""


def test_a_stored_cli_login_counts(tmp_path):
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / ".credentials.json").write_text("{}")
    assert provider_preflight(_env(HOME=str(tmp_path))) == ""


def test_the_launch_refuses_before_it_can_publish_an_outage(monkeypatch):
    """The important half: no flag is touched and no wait is entered.

    Both are what turned one misconfigured process into a host-wide stall, so
    they are asserted rather than left to the docstring.
    """
    # Patch and call through ONE module object, resolved now rather than at this
    # file's import. Another test file reloads the agent module, so a from-import
    # binding here can end up calling a different copy than the one being
    # patched -- which makes the two assertions below pass while checking
    # nothing. Both halves have to come from `ag`.
    from swebench_unified import agent as ag

    stamped: list[int] = []
    waited: list[int] = []
    monkeypatch.setattr(ag, "_note_auth_failure", lambda *a, **k: stamped.append(1))
    monkeypatch.setattr(ag, "_wait_out_auth_outage", lambda *a, **k: waited.append(1))
    monkeypatch.setattr(ag, "provider_preflight",
                        lambda *a, **k: "no provider is configured for the test")
    assert ag.run_agent_step.__globals__ is vars(ag), \
        "the callee must read the patched globals, or this test proves nothing"

    with pytest.raises(ag.AgentAuthError, match="no provider is configured"):
        ag.run_agent_step(system_prompt="s", user_prompt="u", cwd=str(ROOT),
                          timeout_s=5, max_turns=1, allowed_tools=[])
    assert stamped == [] and waited == []


def test_the_outage_stamp_says_why_in_the_log(caplog, monkeypatch, tmp_path):
    """The reason used to travel only inside the exception, which each driver
    turned into a per-cell verdict -- so the one fact an operator needed appeared
    in no log while the host stalled."""
    import logging

    from swebench_unified import agent as ag

    monkeypatch.setattr(ag, "_AUTH_FLAG", tmp_path / "flag")
    with caplog.at_level(logging.ERROR):
        ag._note_auth_failure("ExpiredTokenException: the security token expired")
    assert "ExpiredTokenException" in caplog.text
    assert (tmp_path / "flag").is_file()

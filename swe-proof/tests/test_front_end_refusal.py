# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""An attack the checker could not translate is not a rejection the spec made.

`test_nagini_no_verdict` pins the first half of this: nagini exits 1 -- the
REJECTION code -- when its front end never reached Viper, so a translation
failure must not read as "does not verify". That fixed the case lanes. It left
`check_attack` routing such a file to `verify_completed=False`, i.e. to
INCONCLUSIVE, which fails a mechanized audit role outright.

Inconclusive is the right answer for a timeout: the program is expressible, the
verifier simply did not finish, and it might have verified -- a real weakness
could be hiding behind the wall clock. It is the wrong answer for a front-end
refusal, where no proof obligation about the program exists or ever could. That
attack probed nothing and hides nothing, which is exactly the contract
`admissible=False` already carries for an attack that assumes rather than
establishes.

Both misreadings point opposite ways. Read as a rejection, an `exit 2.
Translation failed ... TOOLING LIMIT` attack is labelled `rejected (same spec,
does not verify -- good)` and counted toward the floor of attacks that are
supposed to have probed the spec, though the specification never performed that
rejection. Read as a timeout, the same attack turns the cell red for a defect
that is not one.
"""
from __future__ import annotations

from swebench_unified import adversary
from swebench_unified.backends.nagini import (
    FAILURE_MARKER, SUCCESS_MARKER, _no_verdict)
from swebench_unified.verify import VerifyResult

XLATE = ("Translation failed\nInvalid program: abstract.predicate.fold "
         "(model.py@241.8)\n")
REJECTED = (f"{FAILURE_MARKER}\nErrors:\nmodel.py:152:16: error: The "
            "postcondition might not hold.\n")


def _r(out: str, rc: int) -> VerifyResult:
    return VerifyResult(rc == 0 and SUCCESS_MARKER in out, 12.0, out, "",
                        timed_out=rc == 124, returncode=rc,
                        no_verdict_detail=_no_verdict(rc, out))


# ---- the property: which non-verdicts could never have gone the other way ----

def test_a_translation_failure_is_a_front_end_refusal():
    r = _r(XLATE, 1)
    assert r.front_end_refusal
    assert r.crashed, "still a non-verdict: this narrows `crashed`, not replaces it"


def test_a_viper_rejection_is_not_a_refusal():
    """The verdict every nagini reject lane rests on."""
    r = _r(REJECTED, 1)
    assert not r.front_end_refusal and not r.crashed


def test_a_timeout_is_not_a_refusal():
    """The whole point of the distinction. A wall clock leaves open whether the
    file would have verified, so it has to stay inconclusive."""
    assert not _r("", 124).front_end_refusal


def test_an_env_problem_exit_is_not_a_refusal():
    """Exit 2 is the wrapper's env-problem code: an accidental non-verdict, which
    a rerun on a healthy host may well turn into a verdict."""
    r = _r("[sbn] verifier env not found", 2)
    assert r.crashed and not r.front_end_refusal


def test_a_jvm_death_is_not_a_refusal():
    """`crashed` catches this from the banner alone, with exit 1 and no detail.
    It is the Viper bridge dying, not the front end judging."""
    r = VerifyResult(False, 3.0, "", "A fatal error has been detected by the "
                     "Java Runtime Environment", returncode=1)
    assert r.crashed and not r.front_end_refusal


def test_the_other_backends_have_no_refusals():
    """velvet and lean set no detail, so this property must be inert for them --
    their exit 1 really is their verifier's rejection."""
    r = VerifyResult(False, 1.0, "error: unsolved goals", "", returncode=1)
    assert not r.front_end_refusal


# ---- the routing: what `check_attack` reports for one ----

def _patched(monkeypatch, result: VerifyResult, *, evasions=()):
    """`check_attack` with only its verifier and its bundle stubbed."""
    class _Sol:
        @staticmethod
        def read_text():
            return "spec"

    class _B:
        solution = _Sol
        class backend:                     # noqa: N801  (mirrors Bundle)
            language = "python"

    monkeypatch.setattr(adversary, "_bundle", lambda *a, **k: _B)
    monkeypatch.setattr(adversary, "same_spec", lambda *a, **k: True)
    monkeypatch.setattr(adversary, "unsound_evasions",
                        lambda *a, **k: list(evasions))
    monkeypatch.setattr(adversary, "_verify_attack", lambda *a, **k: result)


def test_a_refused_attack_is_inadmissible_not_inconclusive(monkeypatch, tmp_path):
    p = tmp_path / "atk_4.py"
    p.write_text("Fold(relations_done(self))\n")
    _patched(monkeypatch, _r(XLATE, 1))
    out = adversary.check_attack("nagini", "django__django-16333", p)
    assert out["same_spec"] and not out["admissible"]
    assert out["verify_completed"], \
        "a refusal is a settled fact about the file, not an unfinished run"
    assert not out["verifies"]
    assert "could not translate" in out["summary"]
    assert "not a valid counterexample" in out["summary"]


def test_a_refused_attack_is_never_scored_as_rejected(monkeypatch, tmp_path):
    """The label the corpus carries. `build_one` writes `rejected (same spec,
    does not verify -- good)` for anything admissible that does not verify, so
    the guard has to fire before that branch can be reached."""
    p = tmp_path / "atk_7.py"
    p.write_text("raise ValueError()\n")
    _patched(monkeypatch, _r(XLATE, 1))
    out = adversary.check_attack("nagini", "django__django-16333", p)
    assert not (out["admissible"] and out["verify_completed"]
                and not out["verifies"]), "that combination IS the reject label"


def test_a_timed_out_attack_stays_inconclusive(monkeypatch, tmp_path):
    """The direction that must not move: `restamp_gate` clears a timeout and a
    lane re-runs it, and reading it as inadmissible would retire the attack."""
    p = tmp_path / "atk_1.py"
    p.write_text("pass\n")
    _patched(monkeypatch, _r("", 124))
    out = adversary.check_attack("nagini", "x", p)
    assert out["admissible"] and not out["verify_completed"]


def test_an_evasion_still_reports_its_own_cause(monkeypatch, tmp_path):
    """Two causes now share `admissible=False`, so each has to stay legible: a
    reviewer reading `sorry` must not be told the file failed to translate."""
    p = tmp_path / "atk_2.py"
    p.write_text("pass\n")
    _patched(monkeypatch, _r(REJECTED, 1), evasions=["dropped an obligation"])
    out = adversary.check_attack("nagini", "x", p)
    assert not out["admissible"]
    assert "assumes rather than establishes" in out["summary"]
    assert "translate" not in out["summary"]


def test_a_real_rejection_is_unaffected(monkeypatch, tmp_path):
    p = tmp_path / "atk_3.py"
    p.write_text("pass\n")
    _patched(monkeypatch, _r(REJECTED, 1))
    out = adversary.check_attack("nagini", "x", p)
    assert out["admissible"] and out["verify_completed"] and not out["verifies"]


def test_a_verifying_attack_is_unaffected(monkeypatch, tmp_path):
    """The only shape that can be a verify-does-not-imply-correct hole. No guard
    added here may stand between it and the candidate lane."""
    p = tmp_path / "atk_5.py"
    p.write_text("pass\n")
    _patched(monkeypatch, _r(f"{SUCCESS_MARKER}\n", 0))
    out = adversary.check_attack("nagini", "x", p)
    assert out["admissible"] and out["verify_completed"] and out["verifies"]

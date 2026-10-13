# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Re-derive an audit gate's status from the agent's SUBMITTED ARTIFACTS.

A recorded pass never comes from what the reviewer agent claimed. The mechanized
roles are scored by re-running the attacks they submitted through the verifier and
the resolve oracle; the judgment roles, which have no executable oracle, are
scored from their verdict string alone. Most of the rest is the reading of an
oracle report that decides whether a rejection implicates the SPEC or only the
auditor's own patch -- both fail the gate, so what it settles is which remedy the
record asks for.
"""
from __future__ import annotations

import os
from pathlib import Path

from .audit_roles import MIN_ATTACKS_DEFAULT, _JUDGMENT_PASS, _MECHANIZED


def _canon(path: str) -> str:
    """An attack's identity, so the falsification floor cannot be padded by
    listing one file twice under two spellings (a.py, ./a.py, d/../a.py)."""
    return os.path.realpath(path)


def _leakage_relaxed(bundle) -> bool:
    """True iff the bundle carries an ACCEPTED relaxed-leakage disposition —
    the SAME condition G-LEAK (gates/leak.py) honors: a recorded G-LEAK status
    of "relaxed", or the `relaxed_leakage` meta flag alongside an in-bundle
    RELAXED_LEAKAGE.md. A relaxed leak is a SEMANTIC leak the human reviewer
    accepted; the leakage panel role (panel_3) must defer to it rather than
    independently re-failing the cell (the leakage panel stays advisory, and
    only G-LEAK is recorded)."""
    try:
        meta = bundle.meta()
    except Exception:
        return False
    if meta.get("gates", {}).get("G-LEAK", {}).get("status") == "relaxed":
        return True
    return bool(meta.get("relaxed_leakage") is True
                and (bundle.root / "RELAXED_LEAKAGE.md").exists())


def _oracle_detail(r) -> dict:
    """The per-instance body of a resolve report, whichever oracle produced it.

    The SWE-bench harness returns `{instance_id: {...}}`; the Pro oracle returns
    the body directly. Both are `ResolveResult.report`.
    """
    rep = r.report or {}
    inner = rep.get(r.instance_id) if isinstance(rep, dict) else None
    return inner if isinstance(inner, dict) else (rep if isinstance(rep, dict) else {})


def _oracle_cannot_refute_here(bundle) -> str:
    """Why a not-resolved verdict on THIS instance carries no information; "" if it does.

    The gold patch is correct by construction, so if the oracle cannot certify IT,
    the oracle cannot refute anything else here either: every patch fails for
    whatever reason gold failed, and "verifies but does not resolve" becomes a
    property of the environment that every attack satisfies. Read as evidence, it
    condemns a sound spec, and the cell cannot recover -- routed to repair, the
    agent correctly declines to weaken a spec that was never implicated.

    The standing example is an instance whose suite needs the network: inside a
    sealed container its tests fail under the GOLD patch, so every attack is
    guaranteed to look like a spec break.

    Reads the recorded G-RESOLVE verdict rather than re-running the oracle: the
    gate has already measured exactly this, and the audit stage only runs after it.
    """
    rec = (bundle.meta().get("gates") or {}).get("G-RESOLVE") or {}
    status = rec.get("status")
    if status is None or status == "pass":
        # No verdict recorded yet (a fresh cell, or a backend with no oracle wired)
        # is not evidence of unfitness -- run_resolve's own `completed` flag still
        # routes a launch that measures nothing to inconclusive.
        return ""
    why = str(rec.get("detail") or rec.get("note") or status)
    return f"G-RESOLVE={status} on the gold patch ({why[:200]})"


def _ungradeable_because_of_the_patch(r) -> str:
    """Why a resolve that produced NO report blames the PATCH; "" if it blames the host.

    The companion to _patch_not_a_faithful_refinement for the case where there is no
    report to inspect. When the harness cannot apply a candidate patch it raises
    before grading anything, so nothing is written -- the same silence as a container
    that never started. run_resolve now reads the cause out of the harness's own run
    log, and that is the only place the two are distinguishable.

    Both stay inconclusive, so this moves no verdict. It decides which remedy the
    record asks for: an unapplicable diff is the auditor's payload to redo, while a
    host failure is a measurement to repeat.

    Which payload mistake it was matters too, and the note is the only place it can
    be read afterwards: run_resolve purges the run directory per attempt, and a
    merged INCONCLUSIVE section keeps the prior role block, so the per-attack line
    that carried the harness's own words is gone by the time anyone looks. A .diff
    on disk that applies cleanly is no evidence that what reached the oracle did,
    and the bare "does not apply" cannot express which of the two happened.
    """
    note = str(getattr(r, "note", "") or "")
    if "Patch Apply Failed" in note:
        # `patch`'s own complaint follows the marker: "Only garbage was found in the
        # patch input", "malformed patch at line N", a context mismatch.
        if "Only garbage" in note:
            # Not a diff at any line: a path that could not be read, an attack
            # file, or prose. The round is re-runnable as-is.
            which = (" — the oracle found only garbage in the payload, so what was "
                     "submitted was not a diff at all")
        elif "malformed patch" in note or "corrupt patch" in note:
            which = (" — the payload's hunk structure does not parse, so the diff "
                     "was truncated or transcribed by hand")
        else:
            which = " — the payload is a diff, but its context does not match"
        return ("the auditor's patch does not apply, so the oracle graded nothing "
                "and the spec is not implicated" + which)
    return ""


def _patch_not_a_faithful_refinement(r) -> str:
    """Why a non-resolving patch condemns the PATCH; "" if it condemns the SPEC.

    An attack claims the spec admits a wrong implementation, and its evidence is a
    repo-level patch embedding that implementation which the oracle then rejects.
    "The spec is too weak" only follows if the patch is a FAITHFUL embedding. If it
    never applied, or it breaks the module so thoroughly that nothing runs at all,
    the oracle rejected the auditor's editing and said nothing whatsoever about the
    specification -- inferring a spec defect from it is a non sequitur.

    Either way the attack blocks a clean pass: an unfaithful one lands in
    `inconclusive_hits`, which fails the gate exactly as a confirmed break does.
    So this cannot let a weak spec through. What it decides is what the recorded
    verdict ASKS FOR -- "strengthen this spec" (REPAIR) or "re-run this audit"
    (REAUDIT). Getting that wrong stalls the cell indefinitely: a repair agent
    handed a sound spec reads the artifacts, correctly refuses to weaken them, and
    nothing moves, round after round.
    """
    d = _oracle_detail(r)
    # swebench: patch_successfully_applied (False also when the test log is
    # unparseable, hence the careful wording). Pro: patch_applied.
    if not d.get("patch_successfully_applied", d.get("patch_applied", True)):
        return ("the oracle found no test log for this patch: it did not apply, "
                "or the test command never ran")
    ts = d.get("tests_status")
    if isinstance(ts, dict):
        p2p = ts.get("PASS_TO_PASS") or {}
        kept = len(p2p.get("success") or [])
        lost = len(p2p.get("failure") or [])
        if lost and not kept:
            # A wrong implementation gets specific behavior wrong. Losing EVERY
            # previously-passing test means the tests stopped running -- an import
            # or collection error the patch introduced, which is a property of the
            # patch and not an implementation the spec admitted.
            return (f"the patch breaks the module: 0 of {lost} PASS_TO_PASS tests "
                    "still run, which is a collection/import failure rather than "
                    "a wrong result")
        return ""
    if "n_required" in d:                      # Pro oracle's grade() detail
        if d.get("n_required") and not d.get("n_passed_required"):
            return (f"the patch breaks the module: 0 of {d['n_required']} required "
                    "tests pass, which is a collection/import failure rather than "
                    "a wrong result")
        return ""
    return ("the oracle report carries no per-test outcome, so the rejection "
            "cannot be attributed to the implementation")


def _oracle_evidence(r) -> str:
    """Which required tests the oracle failed, for the recorded verdict.

    A bare "does not resolve" is not actionable by the next reader: the failing
    test names ARE the counterexample's observable behavior, and they are what
    tells a repair agent which property the spec is missing.
    """
    d = _oracle_detail(r)
    ts = d.get("tests_status")
    parts = []
    if isinstance(ts, dict):
        for key in ("FAIL_TO_PASS", "PASS_TO_PASS"):
            b = ts.get(key) or {}
            bad = list(b.get("failure") or [])
            kept = len(b.get("success") or [])
            if bad:
                shown = ", ".join(bad[:3]) + (f", +{len(bad) - 3} more"
                                              if len(bad) > 3 else "")
                parts.append(f"{key} fails {len(bad)}/{len(bad) + kept}: {shown}")
            elif kept:
                parts.append(f"{key} {kept}/{kept} pass")
    else:
        for key, field in (("FAIL_TO_PASS", "f2p_failing"),
                           ("PASS_TO_PASS", "p2p_failing")):
            bad = list(d.get(field) or [])
            if bad:
                parts.append(f"{key} fails: " + ", ".join(bad[:3])
                             + (f", +{len(bad) - 3} more" if len(bad) > 3 else ""))
    if r.flaky:
        parts.append(f"flaky across {r.attempts} attempt(s)")
    return "; ".join(parts)


def _patch_payload_text(v: str) -> str:
    """A submitted `patches` value, as diff TEXT: read it off disk if the agent
    passed a scratch PATH instead.

    The prompts ask for diff text keyed by attack path, and agents reliably
    submit the path of the .diff file they just wrote. Fed to the oracle that
    one-liner is not a diff, so `git apply` refuses it and the run comes back
    "patch did not apply" -- which `_ungradeable_because_of_the_patch` then
    correctly declines to blame on the spec, so the attack lands INCONCLUSIVE
    and the gate fails with the spec never having been tested -- on a cell whose
    audit otherwise ran to completion.

    Narrow on purpose. Only a value that cannot BE a diff is re-read: a real
    unified diff is multi-line, so anything containing a newline is passed
    through untouched, and the length bound keeps a pathological single-line
    payload from being resolved against the filesystem. Reading the file is
    safe here because the caller derives the verdict BEFORE run_audit's scratch
    dir is cleaned (see run_audit's docstring).

    This only ever converts a non-verdict into a verdict; it cannot turn a
    recorded break into a pass, since a patch that resolves makes its attack a
    correct echo, which is the same conclusion the oracle would have reached on
    the identical text submitted inline.
    """
    # .strip(): a path submitted with surrounding whitespace is still a path, and
    # the alternative is to hand the oracle a one-line non-diff -- the very outcome
    # this exists to avoid. Stripping cannot promote a real diff to a path: a diff
    # keeps its newlines, so the multi-line guard already excluded it.
    bare = v.strip()
    if "\n" not in bare and len(bare) < 500:
        try:
            pf = Path(os.path.realpath(bare))
            if pf.is_file():
                return pf.read_text()
        except (OSError, UnicodeDecodeError, ValueError):
            pass
    return v


def _looks_like_diff(text) -> bool:
    """True iff the string plausibly IS unified-diff text rather than a prose
    description of one. Deliberately loose (headers anywhere in the first 4k):
    a well-formed diff that verifies but genuinely fails to resolve must still
    derive BROKEN -- this guard only screens out payloads git-apply could never
    consume.
    """
    if not isinstance(text, str):
        return False
    head = text.lstrip()[:4000]
    return "diff --git" in head or ("--- " in head and "+++ " in head)


def _derive_audit_verdict(role: str, bundle, payload: dict, *,
                          min_attacks: int = MIN_ATTACKS_DEFAULT,
                          check_attack=None, run_resolve=None,
                          attack_results: dict | None = None) -> tuple[str, str]:
    """Re-derive a gate status from the agent's SUBMITTED ARTIFACTS, not its
    self-reported verdict. Returns (status, note).

    panel_1/eq (mechanized): re-run each submitted attack via check_attack
    (same_spec ∧ admissible ∧ verifies = CANDIDATE). BOTH roles fail a CANDIDATE
    only if its faithful patch also does NOT resolve (verify⇏correct) — a
    resolving candidate is a correct echo of the gold, not a spec weakness.
    A clean pass additionally requires the floor — >= min_attacks ADMISSIBLE
    attacks, the prepatch bug reproduced, and a verifying positive control — else
    INCONCLUSIVE (fail-closed). panel_2/panel_3 (judgment): no executable oracle,
    so the self-report stands — a pass verdict passes, any other non-empty verdict
    is a defect, and only an EMPTY verdict is INCONCLUSIVE. The cited evidence
    fields are advisory context there and must NOT flip a pass to a fail; agents
    fill them with prose saying why they found nothing.
    """
    if role in _MECHANIZED and bundle.backend.name == "ears":
        # No verifier: the mechanized legs are executable PROBES in the
        # instance image (nl_attack.run_probe) instead of same_spec+verify.
        return _derive_ears_verdict(role, bundle, payload,
                                    min_attacks=min_attacks,
                                    run_resolve=run_resolve,
                                    attack_results=attack_results)
    if role not in _MECHANIZED:
        # Judgment roles (faithfulness / leakage) have NO executable oracle, so
        # there is nothing to mechanically re-check — trust the verdict string.
        # A pass verdict passes; any other non-empty verdict is a defect (fail);
        # an empty verdict is INCONCLUSIVE (fail-closed). The evidence fields
        # (diverging_input / leaking_line / counterexample) are advisory context
        # and MUST NOT flip a pass to a fail — agents populate them with prose
        # explaining WHY no defect was found ("None found; only divergence is on
        # an unreachable input"), which is not a contradiction.
        verdict = str(payload.get("verdict", "")).strip().lower()
        if verdict in _JUDGMENT_PASS:
            return "pass", payload.get("notes", "") or f"{role}: no defect found"
        # The leakage panel (panel_3) defers to an ACCEPTED relaxed-leakage
        # disposition: if the human reviewer already accepted this semantic leak
        # (G-LEAK == relaxed / RELAXED_LEAKAGE.md), a LEAKAGE verdict is not a
        # fresh defect. By convention (gates/_audit.py) leakage relaxation is a
        # G-LEAK concept, so the panel is recorded as PASS + note (not "relaxed",
        # which record_audit rejects) — never "fail"; this role is advisory and
        # only G-LEAK is recorded.
        # Requires a NON-EMPTY verdict: an agent that submitted nothing is still
        # INCONCLUSIVE (the audit didn't happen — deferral must not mask it, and
        # the retry loop keys off the INCONCLUSIVE note).
        if verdict and role == "panel_3" and _leakage_relaxed(bundle):
            return "pass", ("panel_3: leakage accepted per RELAXED_LEAKAGE.md"
                            f" (agent flagged: {verdict})")
        if verdict:
            return "fail", (payload.get("counterexample", "")
                            or payload.get("notes", "") or f"{role}: {verdict}")
        if payload.get("_role_error"):
            return "fail", (f"{role}: INCONCLUSIVE — the audit role did not run "
                            f"({payload['_role_error']})")
        return "fail", f"{role}: INCONCLUSIVE (no verdict submitted)"

    backend = bundle.backend.name
    fe = bundle.float_encoding() if backend == "nagini" else None
    # Canonicalize + dedupe so the attack floor can't be gamed by listing the
    # same file N times or via path aliases (a.py, ./a.py, d/../a.py).
    attacks, seen = [], set()
    for a in (payload.get("attacks") or []):
        if not isinstance(a, str):
            continue
        c = _canon(a)
        if c not in seen:
            seen.add(c)
            attacks.append(c)
    # patches keyed by the same canonical path. Both the VALUE's type and its
    # emptiness are screened here, as on the EARS path: the payload is agent JSON,
    # so a non-string (a nested object, a number) would reach the oracle and raise
    # on `.encode`, and a blank-but-truthy string would be filtered out by the
    # harness as an empty prediction -- yielding no report, which reads as a docker
    # failure rather than as the missing attack payload it is. Neither is a verdict
    # about the spec; a screened-out patch lands in "no submitted patch" below.
    patches = {_canon(k): _patch_payload_text(v)
               for k, v in (payload.get("patches") or {}).items()
               if isinstance(k, str) and isinstance(v, str) and v.strip()}
    ctrl_canon = _canon(payload["positive_control"]) if payload.get("positive_control") else ""

    # per-attack outcome label (canonical path -> text), surfaced in verdict.md
    # so each rendered attack shows what the runner concluded about it.
    ar = attack_results if attack_results is not None else {}

    candidates = []          # (path, check-result)
    inconclusive_hits = []
    # An attack that CHANGED the spec probed nothing: it asks a different
    # question, so whether it verifies says nothing about the specification under
    # audit. Counting it toward the falsification floor would let a role pass on
    # attacks that never tested the spec at all, so the floor is counted over the
    # admissible ones -- same spec, verdict reached -- rather than over how many
    # files were submitted.
    admissible = []
    for p in attacks:
        res = check_attack(backend, bundle.instance_id, Path(p), fe)
        if not res.get("verify_completed", True):
            inconclusive_hits.append((p, res.get("summary", "")))
            ar[p] = f"inconclusive ({res.get('summary', 'verify did not complete')})"
            continue
        if not res.get("same_spec"):
            ar[p] = "not a counterexample (changed the spec)"
            continue
        if not res.get("admissible", True):
            # Kept out of BOTH tallies on purpose. Such an attack never reached
            # the verifier, so calling it rejected would credit the spec with a
            # rejection it never made, and calling it a candidate would accuse it
            # of admitting an impl it never saw.
            ar[p] = f"not a counterexample ({res.get('summary', 'inadmissible')})"
            continue
        admissible.append(p)
        if res.get("verifies"):
            candidates.append((p, res))
            ar[p] = "same-spec AND verifies — candidate (resolve-checked below)"
        else:
            ar[p] = "rejected (same spec, does not verify — good)"

    # Both mechanized roles apply the SAME test: a same-spec verifying attack is
    # only a CANDIDATE — a real defect (spec too weak) iff its faithful refined
    # patch does NOT resolve (verify ⇏ correct). A candidate whose patch DOES
    # resolve is a correct "echo" of the gold, not a weakness, so it must not
    # fail the gate. (panel_1 previously failed on ANY candidate, skipping this
    # resolve check that eq — on the identical payload — already performed; that
    # asymmetry false-failed echo attacks. The `weakness` protocol is: CANDIDATE,
    # then show the patch does not resolve.)
    # One question, asked once for the whole battery: can this instance's oracle
    # refute anything at all? If it cannot certify the gold patch it cannot, and
    # then no attack's resolve outcome is evidence about the spec.
    no_refutation = _oracle_cannot_refute_here(bundle)
    for p, _ in candidates:
        patch = patches.get(p)
        # .strip(): a whitespace-only patch is no patch, but it is TRUTHY. Passed
        # to the oracle it is filtered out as an empty prediction, so the harness
        # writes no per-instance report at all and the cell records "resolve did
        # not complete: no report ... harness error or image pull failure" -- an
        # infrastructure story for what is really a missing attack payload. Same
        # inconclusive outcome either way; the difference is that the accurate
        # note sends the next reader to the audit agent instead of to docker.
        if not (patch or "").strip():
            inconclusive_hits.append((p, "verifying attack has no submitted patch"))
            ar[p] = "candidate but no submitted patch — inconclusive"
            continue
        if not _looks_like_diff(patch):
            # Audit agents four times (2026-08-18: 42355d18/velvet, 92db3454
            # x2, 942424e1 round 1) submitted `patches` VALUES as prose
            # descriptions ("SEE FILE ...", "gold patch.diff verbatim ...").
            # git-apply of prose cannot apply, so run_resolve honestly fails --
            # and deriving BROKEN/WEAK from that manufactures a spec-too-weak
            # finding out of a malformed payload. A malformed payload proves
            # nothing about the spec: fail-closed as INCONCLUSIVE instead.
            # _ungradeable_because_of_the_patch reaches the same verdict from the
            # harness's own words; this screens it out before paying for the run.
            inconclusive_hits.append(
                (p, "submitted patches value is not unified-diff text "
                    "(payload malformed)"))
            ar[p] = ("candidate but submitted patch is not a unified diff — "
                     "inconclusive (payload malformed)")
            continue
        if no_refutation:
            inconclusive_hits.append(
                (p, f"the oracle cannot refute on this instance: {no_refutation}"))
            ar[p] = ("candidate; the oracle cannot refute on this instance, so its "
                     f"resolve outcome says nothing about the spec ({no_refutation})")
            continue
        r = run_resolve(bundle.instance_id, patch)
        if r.completed and not r.resolved:
            # The oracle rejected the patch. Before condemning the SPEC, require
            # that it rejected the IMPLEMENTATION: a patch that never applied, or
            # that breaks the module outright, tests the auditor's editing rather
            # than the specification. See _patch_not_a_faithful_refinement -- both
            # branches fail the gate, so this is a routing decision, not a
            # relaxation.
            unfaithful = _patch_not_a_faithful_refinement(r)
            if unfaithful:
                inconclusive_hits.append((p, f"patch not a faithful refinement: "
                                             f"{unfaithful}"))
                ar[p] = ("candidate; its patch is not a faithful refinement of the "
                         f"attack, so the spec is not implicated ({unfaithful})")
                continue
            label = "WEAK" if role == "panel_1" else "BROKEN"
            ev = _oracle_evidence(r)
            ar[p] = (f"{label}: verifies but its refined patch does NOT resolve "
                     "(verify⇏correct)" + (f" [{ev}]" if ev else ""))
            return "fail", (f"{label} (verify⇏correct): {p} verifies but its patch "
                            "does not resolve" + (f" — {ev}" if ev else ""))
        if not r.completed:
            # Attribute it where the harness's run log says it belongs. An
            # unapplicable diff is the auditor's payload to redo, not a host fault,
            # and the two are otherwise identical here: both produce no report.
            unusable = _ungradeable_because_of_the_patch(r)
            if unusable:
                inconclusive_hits.append((p, f"patch unusable: {unusable}"))
                ar[p] = f"candidate; {unusable} — inconclusive ({r.note})"
                continue
            inconclusive_hits.append((p, f"resolve did not complete: {r.note}"))
            # Keep the harness note: "did not complete" alone cannot be triaged
            # later (a timeout, an image pull failure and a wedged host all look
            # identical in verdict.md without it).
            ar[p] = ("candidate; resolve did not complete — inconclusive "
                     f"({r.note})")
        else:
            # Note the flakiness when there was any: an echo that only resolved on
            # a retry is the same measurement that, one attempt short, would have
            # been recorded as a spec defect.
            ar[p] = ("correct echo (verifies AND its patch resolves — not a "
                     "weakness)" + (f" [resolved on attempt {r.attempts}]"
                                    if r.flaky else ""))

    # no confirmed break — require the falsification floor for a clean pass.
    reasons = []
    # An agent that never ran is not an agent that looked and found nothing.
    # "0 admissible attacks of 0 submitted" reads as a reviewer with nothing to
    # say about this spec, and a whole batch of it -- a build started with a PATH
    # that had no agent CLI on it -- reads as a corpus of weak specs. The gate
    # fails either way; what changes is whether the next reader re-runs the audit
    # or goes looking for a defect that was never measured.
    if payload.get("_role_error"):
        reasons.append(f"the audit role did not run ({payload['_role_error']})")
    if len(admissible) < min_attacks:
        reasons.append(f"only {len(admissible)} admissible attacks of "
                       f"{len(attacks)} submitted (need >= {min_attacks} that "
                       "keep the spec and reach a verdict)")
    if not payload.get("prepatch_reproduced"):
        reasons.append("prepatch bug not reproduced")
    if not ctrl_canon:
        reasons.append("no positive control")
    elif ctrl_canon in seen:
        reasons.append("positive control is the same file as an attack")
    else:
        c = check_attack(backend, bundle.instance_id, Path(ctrl_canon), fe)
        if not (c.get("verify_completed", True) and c.get("same_spec") and c.get("verifies")):
            reasons.append(f"positive control did not verify ({c.get('summary','')})")
    if inconclusive_hits:
        # Name WHY, not just how many. This string lands in meta.json and is the
        # only account a later reader has: "1 attack(s) inconclusive" cannot be
        # told apart from an unrunnable oracle, a wedged host or an attack patch
        # that never applied without opening verdict.md, and those want three
        # different remedies. Deduplicated (a battery usually fails the same way
        # for every attack) and bounded, since it is recorded.
        why = "; ".join(dict.fromkeys(w for _, w in inconclusive_hits))[:400]
        reasons.append(f"{len(inconclusive_hits)} attack(s) inconclusive: {why}")
    if reasons:
        return "fail", f"{role}: INCONCLUSIVE — " + "; ".join(reasons)
    return "pass", (f"{role}: {len(admissible)} admissible attacks re-run "
                    f"of {len(attacks)} submitted, none breaks the spec; "
                    "positive control verifies")


def _derive_ears_verdict(role: str, bundle, payload: dict, *,
                         min_attacks: int, run_resolve,
                         attack_results: dict | None) -> tuple[str, str]:
    """Mechanized derivation for the ears backend (no verifier — probes are
    the executable arbiter; docs/architecture.md §6):

    - `attacks` = standalone python probe scripts, each encoding behavior a
      cited requirement MANDATES; run on the gold-PATCHED tree, exit 0 iff it
      holds. A probe that FAILS on the patched tree is a VIOLATION candidate
      (the requirements mandate something the shipped patch does not do) →
      gate fail.
    - `patches` = {name/path → alternative patch diff text} the agent claims
      satisfies every SHALL. Its conformance is checked against the SAME probe
      suite (the payload's own executable reading of the requirements, already
      cross-validated on the gold tree above), then run_resolve: probe-
      conforming AND not resolved → requirements TOO WEAK → gate fail.
    - Floor for a clean pass: >= min_attacks probes; >= 1 candidate patch
      exercised and >= 1 rejected by the probe suite (the weakness search must
      actually happen — probes that merely hold prove conformance, not
      discriminating power); positive control holds on the patched tree AND
      fails at base (the G-DIFF analog, doubling as prepatch_reproduced); no
      inconclusive runs.
    """
    from ..nl_attack import run_probe

    ar = attack_results if attack_results is not None else {}
    probes, seen = [], set()
    for a in (payload.get("attacks") or []):
        if not isinstance(a, str):
            continue
        c = _canon(a)
        if c not in seen:
            seen.add(c)
            probes.append(c)

    inconclusive: list[tuple[str, str]] = []
    for p in probes:
        res = run_probe(bundle.instance_id, Path(p))
        if not res["completed"]:
            inconclusive.append((p, res["summary"]))
            ar[p] = f"inconclusive ({res['summary']})"
            continue
        if not res["holds"]:
            ar[p] = f"VIOLATION: fails on the patched tree ({res['summary']})"
            return "fail", (f"VIOLATION: probe {p} encodes a requirement-"
                            f"mandated behavior that FAILS on the patched "
                            f"tree ({res['summary']})")
        ar[p] = "holds on the patched tree (good)"

    # too-weak candidates: alternative patches claimed to satisfy every SHALL.
    # Agents submit diff TEXT per the prompt, but reliably pass scratch file
    # PATHS instead; `_patch_payload_text` accepts either (it is shared with the
    # mechanized derivation, which had the same payloads and not the tolerance).
    patches = {k: _patch_payload_text(v)
               for k, v in (payload.get("patches") or {}).items()
               if isinstance(k, str) and isinstance(v, str) and v.strip()}
    n_rejected = 0   # candidates the probe suite mechanically rejected
    no_refutation = _oracle_cannot_refute_here(bundle)
    for key, patch_text in patches.items():
        if not _looks_like_diff(patch_text):
            # Same screen as the mechanized lane, and it matters more here: prose
            # handed to run_probe as a candidate patch does not apply, and a probe
            # that then reports "does not hold" would be counted as a candidate
            # the requirements REJECTED -- crediting the suite with discriminating
            # power it never demonstrated.
            inconclusive.append((key, "submitted patches value is not unified-diff "
                                      "text (payload malformed)"))
            ar[key] = ("candidate patch is not a unified diff — inconclusive "
                       "(payload malformed)")
            continue
        conforms, why = True, ""
        for p in probes:
            res = run_probe(bundle.instance_id, Path(p), patch_text=patch_text)
            if not res["completed"]:
                inconclusive.append((key, f"probe {p} under candidate: "
                                          f"{res['summary']}"))
                conforms, why = False, "inconclusive"
                break
            if not res["holds"]:
                conforms, why = False, f"probe {Path(p).name} rejects it"
                break
        if not conforms:
            if why != "inconclusive":
                n_rejected += 1
                ar[key] = f"weak-candidate rejected ({why} — good)"
            continue
        if no_refutation:
            inconclusive.append(
                (key, f"the oracle cannot refute on this instance: {no_refutation}"))
            ar[key] = ("candidate conforms; the oracle cannot refute on this "
                       "instance, so its resolve outcome says nothing about the "
                       f"requirements ({no_refutation})")
            continue
        r = run_resolve(bundle.instance_id, patch_text)
        if r.completed and not r.resolved:
            # Same requirement as the formal backends: the oracle must have
            # rejected the IMPLEMENTATION. A candidate that never applied, or that
            # breaks the module outright, tells us nothing about what the
            # requirements admit. Still fails the gate, as inconclusive.
            unfaithful = _patch_not_a_faithful_refinement(r)
            if unfaithful:
                inconclusive.append((key, f"candidate patch unusable: {unfaithful}"))
                ar[key] = ("candidate conforms but its patch is unusable, so the "
                           f"requirements are not implicated ({unfaithful})")
                continue
            ev = _oracle_evidence(r)
            ar[key] = ("WEAK: satisfies every probe but does NOT resolve "
                       "(requirements admit an incorrect implementation)"
                       + (f" [{ev}]" if ev else ""))
            return "fail", (f"WEAK: candidate patch {key!r} satisfies every "
                            "probe of the requirements yet does not resolve"
                            + (f" — {ev}" if ev else ""))
        if not r.completed:
            inconclusive.append((key, f"resolve did not complete: {r.note}"))
            ar[key] = "candidate conforms; resolve did not complete — inconclusive"
        else:
            ar[key] = "correct echo (conforms AND resolves — not a weakness)"

    # no confirmed break — falsification floor for a clean pass. Probes all
    # holding on the patched tree shows conformance, not falsification power:
    # without exercised WRONG implementations the suite could be restating public
    # behavior. Require the weakness search to have actually happened: >= 1
    # candidate patch exercised AND >= 1 mechanically REJECTED by the probe suite
    # (the analog of the formal floor's verifier-rejected attacks).
    reasons = []
    if len(probes) < min_attacks:
        reasons.append(f"only {len(probes)} probes (need >= {min_attacks})")
    if not patches:
        reasons.append("no too-weak candidate patches exercised (need >= 1 — "
                       "the weakness search did not happen)")
    elif n_rejected < 1:
        reasons.append("no candidate patch was rejected by the probe suite — "
                       "the probes demonstrated no discriminating power "
                       "against wrong implementations")
    ctrl = payload.get("positive_control")
    if not ctrl or not isinstance(ctrl, str):
        reasons.append("no positive control")
    else:
        # Unlike the formal floor (attacks = wrong impls, control = a correct
        # impl — disjoint by nature), an ears control IS naturally one of the
        # probes: it plays both roles (holds-on-patched as an attack probe,
        # fails-at-base as the discriminator). If it was already run as an
        # attack above, its patched-tree result is known — only add the base
        # run.
        cp = Path(_canon(ctrl))
        if _canon(ctrl) in seen:
            on_patched = {"completed": True, "holds": True, "summary":
                          "already ran as an attack probe (held)"}
        else:
            on_patched = run_probe(bundle.instance_id, cp)
        at_base = run_probe(bundle.instance_id, cp, at_base=True)
        if not (on_patched["completed"] and at_base["completed"]):
            # cite the run that actually failed (the patched leg's synthetic
            # "already ran as attack" summary must not mask the base leg)
            bad = on_patched if not on_patched["completed"] else at_base
            reasons.append(f"positive control run inconclusive ({bad['summary']})")
        elif not on_patched["holds"]:
            reasons.append("positive control does not hold on the patched tree")
        elif at_base["holds"]:
            reasons.append("positive control also holds at base — it does not "
                           "discriminate the fix (G-DIFF analog unmet)")
    if inconclusive:
        first = inconclusive[0]
        reasons.append(f"{len(inconclusive)} probe run(s) inconclusive "
                       f"(first: {Path(str(first[0])).name}: {first[1][:160]})")
    if reasons:
        return "fail", f"{role}: INCONCLUSIVE — " + "; ".join(reasons)
    return "pass", (f"{role}: {len(probes)} requirement probes hold on the "
                    f"patched tree; {n_rejected}/{len(patches)} weak-candidate"
                    f"(s) rejected by the probe suite; positive control "
                    "discriminates base vs patched")

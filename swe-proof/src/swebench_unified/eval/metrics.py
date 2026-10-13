# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Verification-effectiveness metrics (verify events matched by ANY backend's
tool name so trajectories from any backend aggregate). Computed from saved
trajectory + grade + status, so recomputable on any past run.

  per_instance_metrics — engagement + grounding signals for one instance.
  aggregate — run rollup incl. the HEADLINE conditional resolve rates
      (resolve | verifying model) vs (resolve | none) — the "does verification
      help?" signal. `format_report` renders it.
"""
from __future__ import annotations

from ..benchmarks import active_workdir
from .adapter import VERIFY_TOOL_NAMES


def per_instance_metrics(trajectory: list, grade: dict, status: dict,
                         workdir: str | None = None) -> dict:
    """Verification signals for one instance. Grounding = model VERIFIED before
    the repo patch was edited (vs post-hoc modelling).

    `workdir`: the benchmark's checkout dir, used to recognise an absolute repo
    path in a bash command; defaults to the active benchmark's
    container_workdir. Metrics run after the container is gone (run.py) and are
    recomputed offline over saved trajectories (report.py), so the value is
    resolved from the registry rather than threaded from a live container."""
    if workdir is None:
        workdir = active_workdir()
    verify_calls = [e for e in trajectory if e.get("kind") in VERIFY_TOOL_NAMES]
    n_verify = len(verify_calls)
    n_verify_ok = sum(1 for e in verify_calls if e.get("ok"))
    verify_wall = round(sum(e.get("wall_s", 0) or 0 for e in verify_calls), 1)

    # ordinal of first verifying model vs first repo-patch edit → model-first
    op = 0
    first_verify_ok_op = None
    first_repo_edit_op = None
    for e in trajectory:
        k = e.get("kind")
        if k in VERIFY_TOOL_NAMES:
            op += 1
            if e.get("ok") and first_verify_ok_op is None:
                first_verify_ok_op = op
        elif k == "bash":
            op += 1
            if first_repo_edit_op is None and _is_repo_patch_edit(e.get("command", ""), workdir):
                first_repo_edit_op = op
        elif k in ("submit",):
            op += 1

    got_verified_model = n_verify_ok > 0
    model_first = bool(got_verified_model and first_verify_ok_op is not None
                       and (first_repo_edit_op is None or first_verify_ok_op <= first_repo_edit_op))

    return {
        "engaged_verification": n_verify > 0,
        "n_verify_calls": n_verify,
        "n_verify_ok": n_verify_ok,
        "verify_wall_s": verify_wall,
        "got_verified_model": got_verified_model,
        "model_first": model_first,
        "submitted_with_model": status.get("submitted") and grade.get("verified") is not None,
        # grade-derived (None where N/A for the mode)
        "resolved": grade.get("resolved"),
        "verified": grade.get("verified"),
        "antifakery_ok": grade.get("antifakery_ok"),
        "equivalent": grade.get("equivalent"),
        "spec_ok": grade.get("spec_ok"),
        "spec_audit": grade.get("spec_audit") or {},
        "passed": grade.get("passed"),
        "steps": status.get("steps"),
        "out_tokens": (status.get("usage") or {}).get("outputTokens"),
        "in_tokens": (status.get("usage") or {}).get("inputTokens"),
        "stop": status.get("stop"),
    }


def _is_repo_patch_edit(cmd: str, workdir: str) -> bool:
    """Heuristic: bash command editing a repo source file (not the model).
    Only feeds the model-first grounding signal.

    An edit counts when it looks like a write AND names either a .py file or an
    absolute path inside the checkout (`workdir`) — cwd-relative edits are
    tolerated by the .py disjunct. The absolute-path disjunct is the reason this
    takes the workdir: hardcoding /testbed made the signal dead on any benchmark
    that checks out elsewhere, which shows up as under-counted grounding rather
    than as an error."""
    c = cmd.lower()
    if "model" in c and ".py" in c:        # writing/patching the model file
        return False
    return (any(tok in cmd for tok in ("sed -i", ".replace(", " > ", ">>", "patch -p", "apply"))
            and (".py" in cmd or f"{workdir.rstrip('/')}/" in cmd))


def _rate(num: int, den: int) -> float | None:
    return round(num / den, 4) if den else None


def aggregate(rows: list[dict]) -> dict:
    """Run rollup over per-instance dicts (state + grade fields + a `metrics`
    sub-dict from per_instance_metrics)."""
    done = [r for r in rows if r.get("state") == "done"]
    n = len(done)
    M = [r.get("metrics", {}) for r in done]

    def cnt(pred):
        return sum(1 for m in M if pred(m))

    resolved = cnt(lambda m: m.get("resolved"))
    passed = sum(1 for r in done if r.get("passed"))

    engaged = cnt(lambda m: m.get("engaged_verification"))
    got_model = cnt(lambda m: m.get("got_verified_model"))
    model_first = cnt(lambda m: m.get("model_first"))
    total_verify_calls = sum(m.get("n_verify_calls", 0) for m in M)
    verify_calls_list = sorted(m.get("n_verify_calls", 0) for m in M)

    # HEADLINE: does a verifying model correlate with resolving?
    with_model = [m for m in M if m.get("got_verified_model")]
    without_model = [m for m in M if not m.get("got_verified_model")]
    res_given_model = _rate(sum(1 for m in with_model if m.get("resolved")), len(with_model))
    res_given_nomodel = _rate(sum(1 for m in without_model if m.get("resolved")),
                              len(without_model))
    lift = (round(res_given_model - res_given_nomodel, 4)
            if res_given_model is not None and res_given_nomodel is not None else None)

    verified = [m for m in M if m.get("verified") is True]
    antifakery = cnt(lambda m: m.get("antifakery_ok") is True)
    equivalent = cnt(lambda m: m.get("equivalent") is True)
    verified_and_resolved = cnt(lambda m: m.get("verified") and m.get("resolved"))

    def median(xs):
        return xs[len(xs) // 2] if xs else 0

    out_tok = sum((m.get("out_tokens") or 0) for m in M)
    in_tok = sum((m.get("in_tokens") or 0) for m in M)
    steps_list = sorted(m.get("steps") or 0 for m in M)

    # mode 8: spec-audit funnel + which property fails most
    spec_props = ("axioms_sound", "admissible", "sound", "complete", "faithful")
    audited = [m.get("spec_audit") or {} for m in M if m.get("spec_ok") is not None]
    spec_block = {}
    if audited:
        spec_ok_cnt = cnt(lambda m: m.get("spec_ok") is True)
        prop_fail = {p: 0 for p in spec_props}
        for sa in audited:
            pf = sa.get("property_fail_votes") or {}
            decisive = (sa.get("yes", 0) + sa.get("no", 0)) or 1
            for p in spec_props:
                if pf.get(p, 0) > decisive / 2:    # majority of decisive ballots failed prop p
                    prop_fail[p] += 1
        spec_block = {
            "spec_pass_rate": _rate(spec_ok_cnt, n),
            "spec_audited": len(audited),
            "spec_property_fail_counts": prop_fail,   # instances failing each property
        }

    return {
        "n_done": n,
        "pass_rate": _rate(passed, n),
        "resolve_rate": _rate(resolved, n),
        "passed": passed, "resolved": resolved,
        # verification engagement
        "verify_engagement_rate": _rate(engaged, n),
        "verified_model_rate": _rate(got_model, n),
        "total_verify_calls": total_verify_calls,
        "mean_verify_calls": round(total_verify_calls / n, 2) if n else None,
        "median_verify_calls": median(verify_calls_list),
        "max_verify_calls": (verify_calls_list[-1] if verify_calls_list else 0),
        # headline conditional resolve rates
        "resolve_rate_given_verified_model": res_given_model,
        "resolve_rate_given_no_verified_model": res_given_nomodel,
        "verification_resolve_lift": lift,          # the key "does it help" number
        "verified_and_resolved_rate": _rate(verified_and_resolved, n),
        # grounding / integrity
        "model_first_rate": _rate(model_first, n),  # model verified before patch edited
        "antifakery_ok_rate": _rate(antifakery, len(verified)) if verified else None,
        "equivalence_rate_among_verified_resolved":
            _rate(equivalent, verified_and_resolved) if verified_and_resolved else None,
        # cost / effort
        "median_steps": median(steps_list),
        "total_output_tokens": out_tok,
        "total_input_tokens": in_tok,
        "total_verify_wall_s": round(sum(m.get("verify_wall_s", 0) or 0 for m in M), 1),
        # spec-generation audit (mode 8 only)
        **spec_block,
    }


def format_report(summ: dict) -> str:
    """Human-readable run report (printed at the end of a run)."""
    a = summ.get("metrics", {})
    mode = summ.get("mode")
    lines = []
    L = lines.append
    L("=" * 66)
    L(f" EVAL RESULTS — run {summ.get('run_id')}  (mode {mode}, model {summ.get('model')})")
    L("=" * 66)
    L(f"  instances: {summ.get('done')}/{summ.get('total')} done"
      + (f"  ·  {summ.get('error',0)} error  ·  {summ.get('creds_expired',0)} parked(creds)"
         if (summ.get('error') or summ.get('creds_expired')) else ""))
    L("")
    L("  OUTCOME")
    L(f"    pass rate ............................. {_pct(a.get('pass_rate'))}"
      f"  ({a.get('passed')}/{a.get('n_done')})")
    L(f"    resolve rate (SWE-bench oracle) ....... {_pct(a.get('resolve_rate'))}"
      f"  ({a.get('resolved')}/{a.get('n_done')})")
    if mode != 0:
        L("")
        L("  FORMAL VERIFICATION — engagement (is it actually used?)")
        L(f"    used the verifier ..................... {_pct(a.get('verify_engagement_rate'))}")
        L(f"    achieved a VERIFYING model ............ {_pct(a.get('verified_model_rate'))}")
        L(f"    verify calls (mean / median / max) .... {a.get('mean_verify_calls')}"
          f" / {a.get('median_verify_calls')} / {a.get('max_verify_calls')}")
        L("")
        L("  FORMAL VERIFICATION — does it HELP? (headline)")
        L(f"    resolve | got a verifying model ....... "
          f"{_pct(a.get('resolve_rate_given_verified_model'))}")
        L(f"    resolve | NO verifying model .......... "
          f"{_pct(a.get('resolve_rate_given_no_verified_model'))}")
        L(f"    >> verification resolve LIFT .......... "
          f"{_signed_pct(a.get('verification_resolve_lift'))}")
        L(f"    verified AND resolved ................. "
          f"{_pct(a.get('verified_and_resolved_rate'))}")
        L("")
        L("  GROUNDING / INTEGRITY")
        L(f"    model verified BEFORE patch (grounded)  {_pct(a.get('model_first_rate'))}")
        if a.get("antifakery_ok_rate") is not None:
            L(f"    model is an honest contract ........... {_pct(a.get('antifakery_ok_rate'))}")
        if mode in (3, 5, 7) and a.get("equivalence_rate_among_verified_resolved") is not None:
            L(f"    judge: model≡patch (verified+resolved)  "
              f"{_pct(a.get('equivalence_rate_among_verified_resolved'))}")
    if mode == 8 and a.get("spec_audited"):
        L("")
        L("  SPECIFICATION AUDIT (mode 8 — funnel + where specs fail)")
        L(f"    witness verifies + honest contract .... {_pct(a.get('verified_model_rate'))}")
        L(f"    SPEC passes audit (axioms∧admiss∧sound∧complete∧faithful)  "
          f"{_pct(a.get('spec_pass_rate'))}")
        pf = a.get("spec_property_fail_counts") or {}
        L("    property failures (instances): " +
          ", ".join(f"{p}={pf.get(p, 0)}" for p in
                    ("axioms_sound", "admissible", "sound", "complete", "faithful")))
    L("")
    L("  COST")
    L(f"    median steps .......................... {a.get('median_steps')}")
    L(f"    output / input tokens ................. {a.get('total_output_tokens'):,}"
      f" / {a.get('total_input_tokens'):,}")
    if summ.get("audit_flagged"):
        L(f"  ⚠ audit-flagged trajectories: {summ['audit_flagged']} (review before trusting)")
    L("=" * 66)
    return "\n".join(lines)


def _pct(x):
    return f"{x*100:5.1f}%" if isinstance(x, (int, float)) else "  n/a"


def _signed_pct(x):
    if not isinstance(x, (int, float)):
        return "  n/a"
    return f"{x*100:+5.1f} pts"

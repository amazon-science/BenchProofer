#!/usr/bin/env python3
"""G-AX for django__django-7530.

The modeled behavior — the enumeration of `(app_label, model_name)` pairs in
makemigrations' consistency check — is modeled DEEPLY over the applications
carrier (`App` / `appPairs` / `pairsSpec` in Solution.lean). The post-patch inner
iterable `apps.get_app_config(app_label).get_models()` is an A-REFERENCE (the
models the application owns), not a consumed axiom: the construction agent ships
no `axiom <callee>_prop`, and the deep model's behavior is validated end-to-end
by G-CONF (conformance_check.py).

Per the worker contract ("If the proof needs no callee axiom, this may be a skip
stub"), this is a skip stub. It also performs a best-effort probe of the REAL
django apps registry to confirm the A-reference's attribution property — the very
property the fix relies on:

    every model yielded by apps.get_app_config(label).get_models()
    has model._meta.app_label == label

(i.e. `get_app_config(label).get_models()` attributes a model only to the app
that owns it). This is the invariant the pre-patch `apps.get_models(app_label)`
call violated (it returned all project models regardless of label). The probe is
guarded so it degrades to a clean skip if the registry is not populated in this
environment.

stdlib-only (django is the system-under-test, already installed in-container).
exit 0 (skip / pass).
"""
import sys


def main():
    try:
        from django.apps import apps as global_apps

        if not global_apps.ready:
            raise RuntimeError("apps registry not populated")

        configs = list(global_apps.get_app_configs())
        if not configs:
            raise RuntimeError("no app configs available")

        violations = 0
        checked = 0
        for cfg in configs:
            label = cfg.label
            for model in cfg.get_models():
                checked += 1
                if model._meta.app_label != label:
                    violations += 1

        if violations:
            print("G-AX FAIL: get_app_config(label).get_models() yielded "
                  "{0} mis-attributed model(s)".format(violations))
            return 1

        print("G-AX OK (probe): attribution property holds on {0} "
              "(app_label, model) observations across {1} apps".format(
                  checked, len(configs)))
        print("status=skip")
        return 0
    except Exception as e:
        print("G-AX skip: no consumed axioms; registry probe unavailable ({0})".format(e),
              file=sys.stderr)
        print("status=skip")
        return 0


if __name__ == "__main__":
    sys.exit(main())

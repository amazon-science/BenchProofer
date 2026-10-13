#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-12713 (plan §4.1).

Refutes (does not prove) the R/I refinement leg of the widget-precedence
decision modeled in Solution.lean (`resolveWidget`). There are NO axioms in this
bundle: every op is closed Option/precedence logic over free inputs (the
caller-supplied widget and the field's computed default), so the whole impl
region is R/I-tagged (conf_skip=false).

  * SHADOW  — Solution.lean's modeled decision (`resolveWidget`) transliterated
              to Python over the real repo types, via the mapping.md §2
              bijection:
                  provided        <->  kwargs.get('widget')  (None | a widget)
                  computedDefault <->  the widget the UNCHANGED autocomplete /
                                       raw_id / filter selection chain would pick
                                       for this field (None when none applies)
              There are NO A-tagged ops (no consumed axioms), so the shadow is
              pure R/I.

  * ORACLE  — `patch.diff`'s behaviour. As with django__django-11095, exercising
              the REAL `ModelAdmin.formfield_for_manytomany` requires a fully
              migrated admin site (a registered ModelAdmin, a model with a M2M
              `_meta`, an AdminSite, a request, and the live widget classes).
              Building that purely to read back which widget lands in `kwargs`
              would not isolate the modeled change, so — per the worker prompt
              (the 11095 ORACLE-choice precedent) — the ORACLE is the patched
              control/data flow transliterated VERBATIM from the gold-patched
              django/contrib/admin/options.py:

                  if 'widget' not in kwargs:
                      autocomplete_fields = self.get_autocomplete_fields(request)
                      if db_field.name in autocomplete_fields:
                          kwargs['widget'] = AutocompleteSelectMultiple(...)
                      elif db_field.name in self.raw_id_fields:
                          kwargs['widget'] = ManyToManyRawIdWidget(...)
                      elif db_field.name in [*filter_vertical, *filter_horizontal]:
                          kwargs['widget'] = FilteredSelectMultiple(...)
                  # ... queryset handling (widget-irrelevant) ...
                  return db_field.formfield(**kwargs)

              The single behavioural change is the `if 'widget' not in kwargs:`
              guard wrapping the selection chain. Everything inside the chain
              (the autocomplete/raw_id/filter membership tests and the widget
              constructors) is UNCHANGED by the patch and only computes WHICH
              default applies — never WHETHER a caller-supplied widget is kept.
              So the chain's result is folded into:
                * provided         — kwargs.get('widget'); None iff 'widget' not
                                     in kwargs (the guard's exact condition).
                * computed_default — the widget that unchanged chain would set
                                     (None when no branch fires).
              and the post-patch resolution is:
                    widget = provided if provided is not None else computed_default
              i.e. `kwargs['widget']` after the guarded chain runs.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample. stdlib only. Fuzz seed pinned
(mapping.md §4).
"""
import random
import sys

SEED = 12713
N_FUZZ = 100_000

# Sentinel widget identities (opaque ids, the mapping.md §2 carrier for Widget).
# None models "no widget"; any non-None object models a distinct widget identity.
_NO_WIDGET = None


# ---- SHADOW: Solution.lean `resolveWidget` transliterated ------------------

def shadow_resolve_widget(provided, computed_default):
    """resolveWidget: caller's widget wins when supplied; else the computed
    default (which may itself be None)."""
    if provided is None:
        return computed_default
    return provided


# ---- ORACLE: patched options.py widget resolution transliterated -----------

def oracle_resolve_widget(provided, computed_default):
    """The patched formfield_for_manytomany widget resolution. `provided` is
    kwargs.get('widget'); 'widget' not in kwargs IFF provided is None. The
    guarded selection chain only runs in that case, and its result is
    `computed_default`. Returns kwargs['widget'] after the chain."""
    # kwargs models a single relevant key: 'widget'. The guard tests membership;
    # we model "absent" as provided is None and "present" as provided not None
    # (a None-valued explicit widget is not something Django's kwargs.get path
    # distinguishes for this code, and the issue/test only set a real widget).
    kwargs = {}
    if provided is not None:
        kwargs['widget'] = provided
    # ---- patched hunk ----
    if 'widget' not in kwargs:
        # autocomplete / raw_id / filter selection chain (UNCHANGED); its net
        # effect for this field is `computed_default`.
        if computed_default is not None:
            kwargs['widget'] = computed_default
    # ---- end hunk ----
    return kwargs.get('widget')


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    # Distinct opaque widget identities. _NO_WIDGET (None) means "no widget".
    # 'CALLER' models a caller-supplied widget (the test's CheckboxSelectMultiple
    # via formfield_overrides); 'AUTO'/'RAWID'/'FILTER' model the three defaults
    # the unchanged chain may pick. They are deliberately distinct so any
    # default-overwrites-caller bug surfaces.
    caller_widgets = ['CALLER', 'CALLER2']
    default_widgets = [None, 'AUTO', 'RAWID', 'FILTER']

    def input_space():
        # Boundary / F2P-shaped cases first (plan §4.1 step 4).
        # F2P: caller provides CheckboxSelectMultiple, field is filter_vertical
        # (so the unchanged chain WOULD pick FilteredSelectMultiple). Patched =>
        # caller's widget must win.
        yield ('CALLER', 'FILTER')
        yield ('CALLER', 'AUTO')
        yield ('CALLER', 'RAWID')
        yield ('CALLER', None)        # caller widget, no default => caller wins
        yield (None, 'FILTER')        # no caller, filter field => default
        yield (None, 'AUTO')
        yield (None, 'RAWID')
        yield (None, None)            # no caller, plain field => None
        # Fuzz: arbitrary (caller, default) pairs over the identity pool.
        for _ in range(N_FUZZ):
            provided = rng.choice([None] + caller_widgets)
            default = rng.choice(default_widgets)
            yield (provided, default)

    for provided, default in input_space():
        count += 1
        shadow = shadow_resolve_widget(provided, default)
        oracle = oracle_resolve_widget(provided, default)
        if shadow != oracle:
            disagreements.append((provided, default, shadow, oracle))
            if len(disagreements) >= 8:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs (seed=%d):"
              % (len(disagreements), count, SEED))
        for prov, dft, sh, orc in disagreements:
            print("  provided=%r default=%r shadow=%r oracle=%r"
                  % (prov, dft, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of resolveWidget agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements "
          "(caller-supplied widget wins; else the unchanged selection chain's "
          "default; else none)." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())

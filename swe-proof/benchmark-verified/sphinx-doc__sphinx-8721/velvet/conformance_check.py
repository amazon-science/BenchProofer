#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-8721 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region
              (`isEbookFormat` / `shouldSuppress` /
              `collectedPages`) transliterated to Python over the *real* repo
              types, via the mapping.md bijection (`app.builder.name` ↔ `fmt`
              as a str; `viewcode_enable_epub` ↔ `ebookOptIn`;
              `hasattr(env,'_viewcode_modules')` ↔ `hasModules`). The observable
              is the GATING DECISION: does the collection step emit any page?
              (`collectedPages(...) != []`).
  * ORACLE  — `patch.diff`'s behaviour: the *real patched*
              `sphinx.ext.viewcode.collect_pages` applied at base_commit (the
              real correctness oracle, G-RESOLVE), driven with a minimal fake
              `app` so that — ABSENT the inserted guards — the generator would
              reach its (unchanged) emission body and yield a page. We observe
              whether it actually reaches the body (emits) or returns early at
              one of the guard lines the patch inserted.

The impl region has NO A-tagged content (no axiomatized callees), so the shadow
is pure R/I (refinement.md §C). The unchanged emission body is tagged I and is
made cheaply observable here (a sentinel highlighter) without altering the
changed guard lines, which run verbatim from the patched source. They must agree
on every input. Exit 0 iff zero disagreements.

Runs in-container (the patched SWE-Bench instance image), stdlib + the real repo
module only. The fuzz seed is pinned (mapping.md §4).
"""
import random
import sys
import types

SEED = 8721
N_FUZZ = 100_000


# --- SHADOW: the impl-region gating decision, transliterated from Lean -------
def shadow_emits(fmt, ebook_opt_in, has_modules):
    """`collectedPages fmt ebookOptIn hasModules generated != []`, i.e. does the
    step emit any page? Transliterates isCombinedFormat / isEbookFormat /
    shouldSuppress / collectedPages (Solution.lean pure region)."""
    is_combined = fmt == "singlehtml"               # isCombinedFormat
    is_ebook = fmt.startswith("epub")               # isEbookFormat
    should_suppress = is_combined or (is_ebook and not ebook_opt_in)
    if not has_modules:
        return False                                # collectedPages -> []
    if should_suppress:
        return False                                # collectedPages -> []
    return True                                     # collectedPages -> generated (non-empty)


# --- ORACLE: the real patched collect_pages, observed for emit-vs-suppress ---
class _BodyReached(Exception):
    """Raised the instant control reaches the unchanged emission body (i.e. no
    guard returned). The patch's guards all `return` BEFORE the body calls
    `status_iterator`, so reaching that call proves no guard fired."""


def _make_app(fmt, ebook_opt_in, has_modules):
    """A minimal fake `app` exercising the REAL patched guard lines. The guards
    read only `app.builder.name`, `app.builder.env`, and
    `env.config.viewcode_enable_epub`; we populate exactly those, plus the few
    attributes the body reads BEFORE `status_iterator` (`highlighter`,
    `get_relative_uri`) so that — absent a guard — execution provably reaches
    that call."""
    config = types.SimpleNamespace(viewcode_enable_epub=ebook_opt_in)
    env = types.SimpleNamespace(config=config)
    if has_modules:
        # one trivial module so modnames is non-empty and the body would yield.
        env._viewcode_modules = {"spam.mod1": ("code", {}, {}, "spam.mod1")}
    builder = types.SimpleNamespace(
        name=fmt,
        env=env,
        highlighter=types.SimpleNamespace(highlight_block=lambda *a, **k: ""),
        get_relative_uri=lambda a, b: "",
        out_suffix=".html",
    )
    app = types.SimpleNamespace(builder=builder, verbosity=0, outdir="/tmp")
    return app


def _make_oracle():
    """Bind the ORACLE around the patched collect_pages. Monkeypatch
    `status_iterator` — the FIRST call the unchanged emission body makes after
    the inserted guards — to raise `_BodyReached`, WITHOUT touching the changed
    top-of-function guard lines, which run verbatim. Reaching it ⇒ no guard
    fired ⇒ the build would emit pages. Importing the module exercises the
    *patched* repo source (the harness has applied patch.diff at base_commit
    before this runs)."""
    from sphinx.ext import viewcode

    def _trip(*a, **k):
        raise _BodyReached()

    viewcode.status_iterator = _trip
    viewcode.should_generate_module_page = lambda app, modname: True

    def oracle_emits(fmt, ebook_opt_in, has_modules):
        app = _make_app(fmt, ebook_opt_in, has_modules)
        gen = viewcode.collect_pages(app)
        try:
            # Drain the generator. If a guard returned, it yields nothing and
            # the generator is exhausted -> emitted=False. If the body is
            # reached, status_iterator raises _BodyReached -> emitted=True.
            for _ in gen:
                return True            # a page was yielded => emitted
            return False               # generator exhausted with no yield
        except _BodyReached:
            return True                # reached the unchanged emission body
        finally:
            gen.close()

    return oracle_emits


# --- fuzz corpus -------------------------------------------------------------
# Modeled domain: BOTH inserted guards are modeled (mapping.md §A "Modeled
# scope") — the single-combined-document guard and the e-book opt-in guard —
# so every format is in scope and the spec and the real patched code must
# agree exactly everywhere.
EXCLUDED = set()


def rand_fmt(rng):
    pool = [
        "html", "dirhtml", "epub", "epub2", "epub3",
        "latex", "text", "man", "json", "xml", "epubfancy", "epu",
        "single", "singlehtml", "htmlhelp", "applehelp", "", "EPUB", "Epub",
        "singlehtml2", "SINGLEHTML",
    ]
    if rng.random() < 0.15:
        # random short token to probe prefix edge cases
        alpha = "abcdehlmnpstu"
        return "".join(rng.choice(alpha) for _ in range(rng.randint(0, 6)))
    return rng.choice(pool)


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4): the issue's exact scenarios and
    # the family/opt-in/no-modules edges.
    boundary = [
        ("epub", False, True),       # the bug scenario: epub, opt-in off => suppress
        ("epub", True, True),        # opt-in on => emit
        ("epub3", False, True),      # versioned family member => suppress
        ("epub3", True, True),       # versioned, opt-in on => emit
        ("html", False, True),       # ordinary html => emit
        ("html", True, True),        # html, flag on => emit
        ("dirhtml", False, True),    # another html-family => emit
        ("latex", False, True),      # non-html => emit
        ("epub", False, False),      # no modules => emit nothing
        ("html", True, False),       # no modules => emit nothing
        ("epu", False, True),        # NOT an epub prefix-match (shorter) => emit
        ("epubx", False, True),      # epub-prefixed variant => suppress
        ("", False, True),           # empty name => emit
        ("singlehtml", False, True),  # single combined document => suppress
        ("singlehtml", True, True),   # combined doc: opt-in irrelevant => suppress
        ("singlehtml", False, False), # combined doc, no modules => nothing
        ("singlehtml2", False, True), # NOT the exact combined name => emit
        ("single", False, True),      # prefix only, not the combined name => emit
    ]
    for t in boundary:
        yield t
    for _ in range(n):
        fmt = rand_fmt(rng)
        if fmt in EXCLUDED:           # outside the modeled domain (see EXCLUDED)
            continue
        yield (fmt, rng.random() < 0.5, rng.random() < 0.85)


def main():
    rng = random.Random(SEED)
    try:
        oracle_emits = _make_oracle()
    except Exception as e:  # pragma: no cover
        print("G-CONF FAIL: could not bind oracle to patched collect_pages: %r" % (e,))
        return 1

    disagreements = []
    count = 0
    for fmt, opt_in, has_mods in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_emits(fmt, opt_in, has_mods)
        try:
            oracle = oracle_emits(fmt, opt_in, has_mods)
        except Exception as e:  # pragma: no cover
            disagreements.append((fmt, opt_in, has_mods, shadow, "EXC:%r" % (e,)))
            if len(disagreements) >= 5:
                break
            continue
        if shadow != oracle:
            disagreements.append((fmt, opt_in, has_mods, shadow, oracle))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for fmt, opt_in, has_mods, sh, orc in disagreements:
            print("  fmt=%r opt_in=%r has_mods=%r shadow=%r oracle=%r"
                  % (fmt, opt_in, has_mods, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of gatedPageEmission agrees with patch.diff "
          "behaviour (emit-vs-suppress) on %d (format, opt-in, has-modules) "
          "inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())

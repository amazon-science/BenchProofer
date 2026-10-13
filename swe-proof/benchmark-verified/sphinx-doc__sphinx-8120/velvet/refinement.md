# refinement.md — sphinx-doc__sphinx-8120

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`buildLocaleDirs` `do` block) plus the `resolve` deep model, and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement), **A** (axiomatized
callee — **A-consumed** where the proof uses an axiom's `ensures`, **A-reference**
where a deep model is validated == the real callee by G-AX), or **I** (identical
concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A-reference + this narrative are audited by **G-AX** and **G-EQ**.
Claim: any impl verifying against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The locale-dir assembly site — `Sphinx._init_i18n` (`sphinx/application.py:296`)

Gold hunk:
```
- locale_dirs = [None, path.join(package_dir, 'locale')] + list(repo.locale_dirs)
+ locale_dirs = [None]  # type: List[Optional[str]]
+ locale_dirs += list(repo.locale_dirs)
+ locale_dirs += [path.join(package_dir, 'locale')]
```

The behavioral change is the **order** of the assembled list: pre-patch the
bundled `package_dir/locale` entry comes *before* the user `repo.locale_dirs`
entries; post-patch the user entries come *before* the package entry. Because
the downstream loader (`locale.init`, site B) searches in list order and the
first directory defining a message wins, the reorder is exactly what lets a
user-provided `sphinx.po` override a built-in message (the issue).

| # | Solution.lean impl op (`buildLocaleDirs`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `sysNone : Dir`; `repoDirs : List Dir`; `packageLocale : Dir` | `None`; `list(repo.locale_dirs)`; `path.join(package_dir,'locale')` | R | `None`-sentinel/dir-path/list ↔ `Dir`/`List Dir` (mapping.md §2). G-CONF bridges `None ↔ sysNone`. |
| A2 | `let mut localeDirs := [sysNone]` | `locale_dirs = [None]` | I | identical: a singleton list of the system-default entry. |
| A3 | `localeDirs := localeDirs ++ repoDirs` | `locale_dirs += list(repo.locale_dirs)` | I | identical concrete list append of the user entries (order preserved). |
| A4 | `localeDirs := localeDirs ++ [packageLocale]` | `locale_dirs += [path.join(package_dir,'locale')]` | I | identical concrete append of the package entry LAST. |
| A5 | `ensures out = sysNone :: (repoDirs ++ [packageLocale])` | the post-patch list value | R+I | pins the exact element ORDER the gold patch produces; the discriminating clause. |

The type-annotation edits — `List[str] → List[Optional[str]]` on `init`
(site B) and the added `Optional` import — change no runtime value (`None` was
already the first element pre-patch) and are observationally the identity; they
are **not** modeled as ops (mapping.md §1, §C below).

Discriminating content of the change — the package entry comes AFTER the user
entries — lives in `out = sysNone :: (repoDirs ++ [packageLocale])`.
`Solution_prepatch.lean` reproduces the pre-patch order
(`[sysNone, packageLocale] ++ repoDirs`) and **fails** that `ensures` clause:
`[sysNone, packageLocale] ++ repoDirs = sysNone :: (repoDirs ++ [packageLocale])`
is unprovable (the lists differ whenever `repoDirs ≠ []`) — G-DIFF.

## B. The search-order callee — `locale.init` (`sphinx/locale/__init__.py:109`)

The downstream consumer of the assembled list. Its only patch hunk is a pure
**type-annotation** change (`List[str] → List[Optional[str]]`) — no behavioral
edit. Its message-lookup *semantics* (search in order; first definer wins; later
dirs are fallbacks) is what makes the A-site reorder observable, so it is modeled
**deeply** by `resolve` (pure region) as an **A-reference**, not consumed as an
axiom.

| # | Solution.lean construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `resolve cat (d::ds) k = (cat d k).orElse (fun _ => resolve cat ds k)` (+ `resolve_append`) | `locale.init`'s `for dir_ in locale_dirs` loop (`gettext.translation` + `add_fallback`) | A-reference | deep model of the unchanged callee's search-order precedence; validated `resolve == init`'s gettext precedence by axiom_check.py (G-AX). No consumed axiom. mapping.md §3.1. |
| B2 | `resolve_user_precedence` lemma | the behavioral payoff: a user-defined message (that the system default lacks) resolves to the user value despite a trailing package entry | A-reference + I | derived purely from B1 + the A5 order; states the abstract property the issue demands. Generic over catalog contents. |

No separate failing prepatch for site B: it is a no-op type annotation plus the
unchanged loader whose semantics live entirely in the `resolve` deep model (a
prepatch must keep the spec byte-identical, G-DIFF). Its soundness is audited by
G-AX; the A-site prepatch already exercises the discriminating order.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The one operation that genuinely *changed* — the
ORDER of the assembled `locale_dirs` list — is modeled directly by concrete list
ops (A2–A4, all **I**) and pinned by the exact-order postcondition (A5). The
loader whose semantics make the order observable is modeled **deeply**
(`resolve`, B1, an A-reference), not hidden behind an axiom about the function
under change. There is no consumed axiom in this bundle. The type-annotation
edits are observational identities, not modeled ops.

## D. verify(Solution) ⇒ resolved

`buildLocaleDirs` verifies only if its output equals the exact ordered list
`sysNone :: (repoDirs ++ [packageLocale])` (A5) — user entries strictly before
the package entry. By R (`None`/dir/list ↔ `Dir`/`List Dir`) the verified
assembly equals the post-patch `locale_dirs` value on every input; by G-AX the
deep model `resolve` equals the real `sphinx.locale.init` search-order precedence
(A-reference), so that order means a user override wins (`resolve_user_precedence`,
the F2P `test_customize_system_message` assertion `app.translator.gettext('Quick
search') == 'QUICK SEARCH'`); by G-CONF the R/I transliteration of the assembly
agrees with `patch.diff`'s behaviour on ≥10⁵ inputs. Therefore a model satisfying
this spec, refined by the map above, is the gold patch up to type refinement and
the audited callee — and the gold patch resolves (G-RESOLVE). Trust points are
exactly the two of plan §1.1: deep-model soundness (G-AX) and refinement fidelity
(this doc, G-EQ + G-CONF).

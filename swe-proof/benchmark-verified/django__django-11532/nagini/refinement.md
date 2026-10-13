# refinement.md — django__django-11532

The operation-by-operation correspondence between `model.py`'s implementation
(the `ascii_compatible_domain` and `cached_host_name` impl regions, and the
`ace_seq`/`ace_encode`/`valid_label` axioms) and `patch.diff` (the gold patch).
Each step is tagged **R** (type refinement), **A** (axiomatized callee — split
into **A-consumed**, where the proof uses the axiom's `Ensures`, and
**A-reference**, where a deep model is validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The new transform — `punycode()` (`django/utils/encoding.py`)

Gold hunk (new helper):
```
+ def punycode(domain):
+     """Return the Punycode of the given domain if it's non-ASCII."""
+     return domain.encode('idna').decode('ascii')
```

| # | model.py impl op (`ascii_compatible_domain`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `domain: List[int]` | `domain` (`str`) argument of `punycode` | R | `str` ↔ `List[int]` code points (mapping.md §2). |
| A2 | `return ace_encode(domain)` | `return domain.encode('idna').decode('ascii')` | A-consumed | `ace_encode`/`ace_seq` is the **weakest** contract on the unchanged stdlib callee `str.encode('idna').decode('ascii')` the proof needs: a fresh ASCII list equal to the ACE of the label, (the consumed property) **all-ASCII**, and the codec's out-of-band condition on a label with no ACE. The proof consumes `Ensures(all_ascii(...))`, `Ensures(ToSeq(Result()) == ace_seq(...))`, `Ensures(valid_label(ToSeq(domain)))` and the complementary `Exsures(...)`. G-AX runs the real callee and confirms all of them, on both sides of the partition. |
| A3 | *no* handler around the call — the out-of-band condition propagates, pinned by `Exsures(LabelNotEncodable, … and not valid_label(ToSeq(domain)))` | the gold helper's body has **no** `try`/`except`: `UnicodeError` from the codec propagates to `punycode`'s caller | I (control flow) | The gold helper's totality behaviour is *observable*, not incidental: on a label the codec rejects it yields **no value** and the condition reaches its caller. The model states exactly that, in both directions — a value comes back only for a label that has an ACE (`Ensures(valid_label(ToSeq(domain)))`), and every other label is reported out of band with the label unchanged. `LabelNotEncodable` is a *user-defined* exception only because a builtin exception in an `Exsures` crashes the Nagini translator; nothing in the spec pins its identity, message, or any other incidental detail — only which of the two outcomes occurred. |

**Why totality is part of the contract and not excluded by a precondition.**
The label shape is *unrestricted* input: the model's `Requires` clauses on the
two modeled functions constrain permissions only. The gold helper is called from
five sites, and at four of them (section C) the call sits inside an
`except UnicodeError:` arm whose purpose is to *observe* the condition — a
transform that swallowed it and answered with a substitute value (`''`, the
input, a stand-in host name) would make those four sites treat an
un-encodable domain as a valid one, and would cache a stand-in name at the fifth.
That difference is behaviour, so the spec must be able to see it: hence the
complementary pair (normal-return `Ensures(valid_label(…))` /
`Exsures(… not valid_label(…))`) rather than a precondition that would make the
condition unobservable. G-AX confirms the real codec really does partition its
input this way (both tallies non-empty); G-CONF diffs the shadow against the real
repo functions on **both** sides.

## B. The cached-host-name site — `CachedDnsName.get_fqdn` (`django/core/mail/utils.py:14-17`)

Gold hunk (the F2P-tested change):
```
- self._fqdn = socket.getfqdn()
+ self._fqdn = punycode(socket.getfqdn())
```

| # | model.py impl op (`cached_host_name`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | parameter `platform_name: List[int]` | `socket.getfqdn()` (`str`) | R + A-reference-of-input | the platform-reported host name; an unchanged callee whose **return** is the modeled input (mapping.md §2). `socket.getfqdn` is not changed by the patch; only its result is wrapped. Modeling its return as the function input is sound because the spec quantifies over all possible returns (incl. the non-ASCII `漢字` the F2P mocks). |
| B2 | `return ascii_compatible_domain(platform_name)` | `punycode(socket.getfqdn())` | I (call) + A-consumed (callee body) | the cached value is the transform applied to the platform name — literally the gold's composition. `ascii_compatible_domain` is the model of `punycode` (site A); the call is identical control flow. The proof carries the all-ASCII / ACE-value postcondition from site A's contract. |
| B3 | *no* handler around the call — `Exsures(LabelNotEncodable, …)` and `Ensures(valid_label(ToSeq(platform_name)))` | the gold assignment `self._fqdn = punycode(socket.getfqdn())` has **no** `try`/`except`: the codec's condition propagates out of `get_fqdn` and **nothing is cached** | I (control flow) | The gold hands the platform-reported name to the transform *exactly as reported* and caches whatever comes back. So a platform name with no ACE produces no cached value and the condition reaches `get_fqdn`'s caller; the model states that, and states the complement (a cached value exists only for a name that has an ACE), so no stand-in name can be cached in place of one that has none. |

The discriminating content of the change lives in
`Ensures(all_ascii(ToSeq(Result())))` and
`Ensures(ToSeq(Result()) == ace_seq(ToSeq(platform_name)))`: the cached host
name must be the all-ASCII ACE of the platform name. The pre-patch
`self._fqdn = socket.getfqdn()` cached the **raw** name with no transform;
`model_prepatch.py` reproduces that (returns a verbatim copy of `platform_name`)
and **fails** the postcondition `ToSeq(Result()) == ace_seq(ToSeq(platform_name))`
(equivalently `all_ascii`), which is exactly the spec sensing the bug (G-DIFF).
For the F2P witness this is `xn--p8s937b` (all-ASCII) vs the raw `漢字`
(non-ASCII) — the latter is what crashed the iso-8859-1 header serialisation.

## C. The four behaviour-identical call-site swaps (not separately modeled)

The gold patch also rewrites four pre-existing sites that already performed the
ACE transform under a guard, replacing the inline
`domain.encode('idna').decode('ascii')` with a `punycode(...)` call:

- `sanitize_address` (`django/core/mail/message.py`): the
  `try: domain.encode('ascii') except UnicodeEncodeError: domain = domain.encode('idna')…`
  block becomes `domain = punycode(domain)`;
- `URLValidator.__call__` and `EmailValidator.__call__`
  (`django/core/validators.py`): `netloc/domain_part.encode('idna').decode('ascii')`
  → `punycode(...)`;
- `urlize`'s `unquote_quote` and `is_email_simple` (`django/utils/html.py`):
  `netloc/domain.encode('idna').decode('ascii')` → `punycode(...)`.

These are **pure callee extractions** of the SAME expression the new helper
contains (`x.encode('idna').decode('ascii')`) — a refactor that introduces no
new observable behaviour on the tested inputs (an ASCII label's ACE is itself;
the surrounding try/except control flow is preserved verbatim around the call).
They are covered by the same `ace_seq`/`ace_encode` axiom (site A) and are not
exercised by any FAIL_TO_PASS test, so they need no separate failing
`model_prepatch`: there is no independently-observable fixed behaviour at these
sites (the single F2P-observable fix is site B). Modeling site A (the helper)
captures their content; modeling site B captures the one tested behaviour
change.

These four sites are, however, what makes site A's **totality** behaviour
load-bearing rather than decorative, and they are why the model states it (A3):
each of them keeps its surrounding `except UnicodeError:` arm around the
extracted call, so the arm can only still run if the extracted transform lets
the condition through. A helper that returned a substitute value instead would
silently change the control flow of all four — `URLValidator.__call__` and
`EmailValidator.__call__` would stop rejecting an un-encodable domain,
`urlize` would rewrite a link it should have left alone — while still producing
the same values everywhere the codec succeeds. The spec's complementary
outcome pair is exactly the observable that separates the two.

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A, or I. The one operation that genuinely *changed* at
the tested site — applying the ACE transform to the cached host name where the
pre-patch applied nothing — is modeled as the verified **composition** of the
all-ASCII-guaranteeing transform (site A, `ascii_compatible_domain`) with the
platform name (site B). The ACE algorithm itself is an **unchanged stdlib
callee** the new code *calls* (`str.encode('idna')`), legitimately axiomatized
as `ace_seq`/`ace_encode` (A-consumed); there is no axiom about the function
under change (the helper / `get_fqdn` are modeled, not axiomatized).

## E. verify(model) ⇒ resolved

`cached_host_name` verifies only if its result is the **all-ASCII** ACE of the
platform name (B2): a wrong impl that returns the raw name (the bug) cannot
prove `all_ascii` / `ace_seq`-equality, and one that returns arbitrary ASCII
cannot prove `ToSeq(Result()) == ace_seq(ToSeq(platform_name))` (the value is
pinned to the real transform, not an oracle constant — directive 8). It also
verifies only if it reproduces the gold's **outcome partition** (A3/B3): an impl
that answers a name with no ACE with a value of its own cannot prove
`Ensures(valid_label(ToSeq(platform_name)))`, and one that withholds a value
from a name that has one cannot prove the `Exsures`' `not valid_label(…)`. So the
two ways of diverging from the gold's control flow — swallowing the condition and
over-signalling it — are each refuted by one half of the pair. By R
(`str` ↔ `List[int]`; `socket.getfqdn()`-return ↔ input; caching = value
identity) the verified function equals `punycode(socket.getfqdn())` on the
tested inputs; by G-AX the `ace_seq`/`ace_encode` axiom over-approximates the
real `str.encode('idna').decode('ascii')` (all-ASCII on well-formed labels,
`漢字`→`xn--p8s937b`). Therefore a model satisfying this spec, refined by the
map above, is the gold patch up to type refinement and the audited stdlib
callee — and the gold patch resolves (G-RESOLVE). The trust points are exactly
the two of PLAN §1.1: axiom soundness (G-AX) and refinement fidelity (this
document, G-EQ).

# mapping.md — django__django-14855

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 475cffd1d64c690cdad16ede4d5e81985738ceb4`, states the type
abstraction, and gives the provenance of the one axiom (callee source + the
exact behaviour the axiom encodes).

Repo file under change: `django/contrib/admin/helpers.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `related_link_target(names, prefixes, exposes, default_idx, current_idx)` | `AdminReadonlyField.get_admin_url(self, remote_field, remote_obj)` — `django/contrib/admin/helpers.py:206` (changed body line 212) | the modeled changed function (builds the link to a read-only related object) |
| `resolve_prefix(names, prefixes, exposes, default_idx, selector, has_selector)` *(axiom — A-consumed)* | `django.urls.reverse(viewname, …, current_app=…)` — `django/urls/base.py:27` (the namespace→instance selection loop, lines 41–84, and the in-instance identifier lookup it delegates to, `_reverse_with_prefix`) | unchanged framework callee; the patch adds the `current_app=` argument to its call |

The repo objects the model abstracts:
- `self.model_admin.admin_site.name` — the name of the admin-site instance
  currently rendering the page (`ModelAdmin.admin_site` is the `AdminSite`;
  `AdminSite.name` is set in `django/contrib/admin/sites.py:75`). Modeled as
  `names[current_idx]` (the current deployment's instance name).
- `url_name = 'admin:%s_%s_change' % (app_label, model_name)` — the view
  identifier (`helpers.py:207-210`). Its leading `admin:` is the shared
  *application* namespace under which every `AdminSite` registers its URLs
  (`AdminSite.urls` returns `(get_urls(), 'admin', self.name)` —
  `sites.py:303`; the second element `'admin'` is the app namespace, the third
  `self.name` is the per-instance namespace). Modeled as the shared app
  namespace whose registered sibling instances are `names`/`prefixes`/`exposes`.
- whether a given deployment carries a route for that identifier at all. Each
  `AdminSite` builds its URLpatterns from its OWN `_registry`
  (`AdminSite.get_urls`, `sites.py:253`: it iterates `self._registry.items()`),
  so `admin:<app>_<model>_change` exists under a site only if that site
  registers that model. Modeled as `exposes[k]` — deployment `k` carries a route
  for the identifier and argument being resolved. This axis is not hypothetical:
  the gold `test_patch` itself has to ADD `site2.register(...)` calls before the
  custom-site link renders, and its F2P asserts the NO-LINK rendering for a
  related model the site does not register.
- `try: url = reverse(...) / except NoReverseMatch: return str(remote_obj)`
  (`helpers.py:211-216`) — the arm taken when the identifier does not resolve
  inside the selected deployment. NOT abstracted away: it is exactly what the
  EMPTY result denotes (see §2), so the fork is observable in the modeled
  return value.
- `quote(remote_obj.pk)` / `format_html('<a href="{}">{}</a>', url, remote_obj)`
  — unchanged surrounding operations the patch does not touch; they do not
  affect WHICH instance's prefix a produced URL carries, so they are abstracted
  away (the observable the F2P test asserts is the `href` prefix
  `/namespaced_admin/` vs `/admin/`, or the absence of an `href` altogether).
  `quote` does participate in one direction: an argument the route's converter
  rejects makes the identifier unresolvable for that deployment, which is a
  route-axis (`exposes`) observation, and G-CONF observes it rather than
  assuming it.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| an admin-site instance name (`str`, e.g. `"admin"`, `"namespaced_admin"`) | `PSeq[int]` of Unicode code points | `name[k]` ↔ code point; equality of names ↔ `PSeq` equality |
| the mount prefix / produced URL (`str`, e.g. `/admin/…`, `/test_admin/admin5/…`) | `PSeq[int]` | the produced link string ↔ its code-point sequence; the F2P observable is the prefix |
| the registry of sibling instances under the shared `admin` app namespace (Django's `resolver.app_dict['admin']` instance list + their mount prefixes + their route tables) | parallel pure sequences `names : PSeq[PSeq[int]]`, `prefixes : PSeq[PSeq[int]]`, `exposes : PSeq[bool]` | index `k` ↔ the k-th registered instance; `names[k]`/`prefixes[k]`/`exposes[k]` are its name / prefix / whether it carries a route for the identifier and argument at hand |
| "this deployment exposes a change view for the related model, for this pk" (`admin:<app>_<model>_change` resolvable under instance `k` with that argument) | `exposes[k] : bool` | `True` ↔ `reverse` finds the identifier inside instance `k`; `False` ↔ it raises `NoReverseMatch` there |
| **no link at all** — the page renders `str(remote_obj)` because `reverse` raised `NoReverseMatch` (`helpers.py:215-216`) | the EMPTY `PSeq` (`len(Result()) == 0`) | "produced no prefix". Unambiguous because a produced URL always carries the resolution root, so no registered deployment's prefix is empty — stated as the modeled precondition `Forall k: len(prefixes[k]) > 0` and checked against the real callee at its root-mount edge (a deployment mounted at `/` has prefix `/`, length 1) |
| `self.model_admin.admin_site.name` (the current deployment) | `names[current_idx]`, `0 ≤ current_idx < len(names)` | the current instance's name |
| the registered default instance (the one Django’s reverse falls back to with no `current_app`) | `default_idx`, `0 ≤ default_idx < len(names)` | an existential placeholder: the model never fixes WHICH physical index is the default; it only states one exists and that the no-selector path resolves against it. (Django’s rule is the `elif ns not in app_list: ns = app_list[0]` arm of `reverse` — so it is `app_dict[app][0]`, the last-registered instance, ONLY when no sibling is named like the app namespace itself; when one IS (e.g. an `AdminSite(name='admin')` under the `admin` app namespace) that instance is the default instead, since the `elif` never fires. An iteration-order/name-collision detail the proof never relies on, which is exactly why the model leaves the index existential; the `has_selector` branch is the only one the fix exercises.) |
| `str` indexing/iteration | banned in Nagini → `PSeq[int]` carriers throughout | — |

Name uniqueness (`Forall2 … names[a]==names[b] ⇒ a==b`) is a modeled
precondition: distinct admin-site deployments carry distinct `name`s (an
`AdminSite`’s instance namespace is its `name`), so a `current_app` selector
names at most one instance. This is what lets the `has_selector` Forall in the
axiom pin `resolve_prefix`'s result to exactly the current deployment's outcome.

Non-empty prefixes (`Forall k: len(prefixes[k]) > 0`) is the second modeled
precondition on the registry, and it is what makes the empty-`PSeq` carrier for
"no link" faithful rather than merely convenient: a URL Django produces begins
at the resolution root, so every registered deployment contributes at least `/`.
Without it, "produced nothing" and "produced a deployment whose prefix happens
to be empty" would be the same value and the two `len(Result()) == 0` clauses
would be weaker than they read.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `resolve_prefix` ↔ `django.urls.reverse` (A-consumed)
**Callee:** `django.urls.reverse(viewname, urlconf=None, args=None,
kwargs=None, current_app=None)` — `django/urls/base.py:27`. The patch does NOT
change `reverse`; it adds the `current_app=self.model_admin.admin_site.name`
keyword to the existing call. The axiom encodes the namespace→instance
selection `reverse` performs AND the in-instance lookup that follows it — the
weakest contract the proof needs:

```python
# django/urls/base.py (reverse), namespace resolution loop:
*path, view = viewname.split(':')          # 'admin:..._change' -> path=['admin']
if current_app:
    current_path = current_app.split(':'); current_path.reverse()
else:
    current_path = None
for ns in path:                            # ns = 'admin' (the app namespace)
    current_ns = current_path.pop() if current_path else None
    app_list = resolver.app_dict[ns]       # the sibling instance namespaces
    if current_ns and current_ns in app_list:
        ns = current_ns                    # <-- pick the named instance
    elif ns not in app_list:
        ns = app_list[0]                   # <-- no selector: default = app_list[0]
    extra, resolver = resolver.namespace_dict[ns]   # that instance's prefix
...
return resolver._reverse_with_prefix(view, prefix, *args, **kwargs)  # may RAISE
```

So:
- `current_app=<instance name registered under the app namespace>` ⇒ that
  instance's namespace is chosen ⇒ that instance's mount prefix is used
  (`if current_ns and current_ns in app_list: ns = current_ns`). This is the
  axiom's `has_selector` clause and the ONLY selection branch the proof consumes
  — the fix always supplies the current site's name.
- `current_app=None`/falsy ⇒ `current_path = None` ⇒ `current_ns = None` ⇒
  `ns = app_list[0]` (the registered default). This is the axiom's
  `not has_selector` clause (used to characterize the pre-patch path, and to
  characterize an empty selector — see "Falsiness dependency").

The axiom is the **weakest** contract these facts require, not a full model of
`reverse` (URL pattern matching, argument substitution, `get_ns_resolver`, etc.
are all abstracted — they do not change WHICH prefix a produced URL carries, nor
WHETHER one is produced, beyond the single `exposes` bit).

**Partiality (the callee narrows FIRST, then looks up — load-bearing).**
Selection and lookup are sequential and not interchangeable: the loop above
narrows `resolver` down to ONE instance namespace, and only then does
`_reverse_with_prefix` search that resolver's `reverse_dict` for the view
identifier. A `NoReverseMatch` from the final line is therefore a statement
about the SELECTED instance alone — an identifier a SIBLING deployment carries
but the selected one does not raises it, and `reverse` never consults the
sibling. `get_admin_url` catches exactly that (`helpers.py:215-216`) and renders
the related object with NO link.

Resolution is thus a PARTIAL function of the registry, and the axiom says so:
each of its two selection branches has TWO production clauses, "the selected
instance's prefix" when `exposes[selected]` and "nothing" (the empty sequence)
when not. Modelling it as total would be strictly stronger than the callee on a
reachable, in-domain input — see the recorded G-CONF/G-PANEL history at the end
of this file. The consumer's postcondition mirrors the same four cases; the four
guards are pairwise disjoint and jointly total, so the returned value stays
fully pinned and nothing is left free.

The route axis is a first-class part of the repo's own reality, not an edge case
manufactured for the model: sibling `AdminSite`s each have their own `_registry`
(`sites.py:112` `register`, `sites.py:253` `get_urls`), the gold `test_patch`
must ADD `site2.register(...)` calls before the custom-site link renders at all,
and the F2P asserts the no-link fallback for an unregistered target.

**Domain dependency (the `split(':')` fixed-point — load-bearing).** Before any
matching, `reverse` does `current_app.split(':')` (`base.py:42`, quoted above)
and resolves the selector COMPONENT-WISE down the namespace path. A
`current_app` that embeds the `:` component separator is therefore decomposed
into parts and is NOT matched as a whole instance name: a registered instance
whose `name` contains `:` (e.g. `AdminSite(name='a:b')`, a legal, unvalidated
deployment) is *unreachable* as a whole-name selector and falls back to the
default (`app_dict[app][0]`). So the `has_selector` Ensures
(`names[k] == selector ⇒ …prefixes[k]`) holds ONLY when `selector` is
separator-free. The axiom encodes this as a `Requires` on `resolve_prefix`:
every code point of `selector` is `≠ 58` (`:`). This is the input-key analogue
of the `html.escape`/`quote=True` flag dependency in SPEC_GUIDE §3 — when a
callee transforms a string argument before lookup, the axiom must restrict that
argument to the transform's fixed-point domain. The consumer
(`related_link_target`) discharges this `Requires` with a matching precondition:
the current deployment's instance name (`names[current_idx]`, which IS the
selector) is separator-free. The F2P deployment names (`admin`,
`namespaced_admin`) are colon-free, so the restriction is satisfiable and the
modeled behaviour for the tested case is unchanged.

**Falsiness dependency (the second transform-domain fact — load-bearing).**
Before splitting anything, `reverse` guards on `if current_app:`
(`base.py:41`, quoted above). An EMPTY selector is falsy, so `current_path`
stays `None`, the selector never reaches the name matching at all, and
resolution takes the same no-selector fallback arm. An `AdminSite(name='')` is
legal and unvalidated (`sites.py:36`, `def __init__(self, name='admin')`) and
its empty instance namespace really is registered — reachable as
`reverse(':<view>')` — so this is a reachable deployment, not a degenerate one.
Empirically at `base_commit`: with siblings
`{'' → /emptyfirst/ (non-default), 'plain' → /plainmount/, 'last' → /lastmount/}`,
`reverse('admin:<view>', current_app='')` returns `/lastmount/` (the default),
NOT `/emptyfirst/`.

Unlike the `:` case this is NOT excluded from the domain — an empty instance
name is a real deployment the consumer can be rendering under, so excluding it
would hide real behaviour. Instead the axiom MODELS it: the `has_selector`
clauses are restricted to a NON-EMPTY selector (`has_selector and
len(selector) > 0`), and the default clauses absorb the empty selector
(`not has_selector or len(selector) == 0`), which is exactly what the guard
does. Note the consequence for the route axis: on that leg it is the DEFAULT
deployment's route table that decides whether any link is produced, not the
current deployment's — the model's fourth clause, and the one the
`weak-route-axis-swapped` rival in `properties.py` exists to defend.

**Soundness counterexamples (why each domain restriction is real, not
cosmetic).** Empirically against the real callee at `base_commit`:
  * colon: with siblings `{'a:b' → /colon1/ (non-default), 'plain' → /plain/,
    'third' → /third/}`, `reverse('the_app:obj_change', current_app='a:b')`
    returns `/third/` (the default), NOT `/colon1/`. An unrestricted axiom
    claiming the matching `k`'s prefix (`/colon1/`) would be strictly stronger
    than the real callee — unsound. The colon `Requires` excludes exactly this.
  * partiality: with the identifier carried by a sibling but NOT by the selected
    deployment, `reverse(view, current_app=<the selected deployment>)` raises
    `NoReverseMatch` — it does not fall back to the sibling that has it. An
    axiom claiming a prefix there would be unsound; the `exposes` clauses state
    the real outcome.

**Soundness check (G-AX):** `axiom_check.py` builds real Django URLconfs whose
entries are the exact 3-tuple `AdminSite.urls` returns — `(get_urls(), 'admin',
self.name)` (`sites.py:303`) — several sibling instance namespaces under ONE
shared `app_name` (`'the_app'`) mounted at different path prefixes, i.e. exactly
the multiple-`AdminSite` deployment pattern. Nine registry shapes, and crucially
each sibling gets its OWN inner URLconf with its OWN route set (a staircase of
three view names), so the route axis is genuinely observable: with one shared
inner module every sibling would carry identical routes and the axiom's two
"no url" clauses could never be exercised. `exposes[k]` is OBSERVED, never taken
from the literal route set — by reversing against a ONE-deployment URLconf
holding deployment `k`'s route set, where there is nothing to select, so the
observation cannot depend on the selection mechanism under test. (Reversing
through a deployment's own instance namespace cannot serve here: a colon-bearing
instance name is not addressable that way, since the view identifier is split on
`:` too. An earlier version of the G-CONF bridge used that route and
mis-observed a colon-named default — see the recorded history below.) The shapes
also include an empty-named sibling, a sibling named like the shared app
namespace, and a ROOT-mounted deployment (the non-empty edge of the
non-empty-prefix domain fact). It then drives the REAL `django.urls.reverse`:
  * `reverse(view, current_app=<each separator-free instance name>)` ⇒ asserts
    the URL carries THAT instance's prefix when the instance carries the route,
    and that NO url is produced (`NoReverseMatch`) when it does not — with the
    failure message naming the siblings that DO carry it, since a url there
    would mean the callee consulted a sibling;
  * `reverse(view)` (no `current_app`) ⇒ the same two clauses for the registered
    default, whose index is discovered empirically from the no-selector path
    with an anchor route every deployment carries — never hard-coded;
  * `reverse(view, current_app='')` ⇒ asserts it agrees with no `current_app` at
    all, in both route states (the falsiness dependency);
  * **domain boundary:** `reverse(view, current_app='a:b')` ⇒ asserts the URL
    does NOT carry `/colon1/` as a whole-name match and instead behaves as the
    default fallback — i.e. the colon-named instance is split
    (`'a:b'→['a','b']`) and unreachable as a whole-name selector, so an
    unrestricted axiom would over-claim. This validates the
    `selector`-has-no-`:` `Requires`;
  * **colon-separator fuzz:** ~1300 randomized `:`-bearing selectors, each
    asserted NOT to select the colon instance's prefix via a whole-name match;
  * **selection fuzz:** 2000 randomized `(instance, identifier, argument)`
    draws, each checked against the freshly observed route flag.
  Both domain premises (unique names; non-empty prefixes) are ASSERTED of every
  shape rather than assumed, and per-leg coverage counters are asserted non-zero,
  so a probe that silently stopped exercising the no-url clauses FAILS instead of
  passing vacuously. Recorded run: **2996 observations, 0 violations**, coverage
  `{sel_route 32, sel_noroute 13, nosel_route 18, nosel_noroute 9,
  emptysel_route 18, emptysel_noroute 9, colon_boundary 6, rootprefix 1}`.
It imports only `django` (the framework the patch calls); nothing repo-test
specific.

## G-CONF — differential conformance (`conformance_check.py`)

**Pinned fuzz seed: `14855`** (module constant `SEED`). Input count: `100000`
Requires-satisfying observations (`1350` boundary + seeded fuzz to fill).

**Oracle — the real patched function, CALLED (not transliterated).**
`AdminReadonlyField.get_admin_url(self, remote_field, remote_obj)` —
`django/contrib/admin/helpers.py:206` (changed body line 212), i.e. §1's repo
symbol. The gate applies `patch.diff` to `/testbed` first; the script asserts
(*fidelity gate 0*) that the loaded function's source really does forward
`current_app`, so a mis-applied patch fails loudly instead of passing vacuously.
`get_admin_url` reads only `self.model_admin.admin_site.name`,
`remote_field.model._meta.{app_label,model_name}` and `remote_obj.pk` /
`str(remote_obj)`, so it is driven via the unbound function on a duck-typed
receiver — the `url_name` concatenation, the `quote()`, the `current_app=`
argument, the `format_html` wrap and the `NoReverseMatch` fallback are all the
repo's own code, executed as written. In particular the no-link outcome is the
repo's own `return str(remote_obj)`, observed as "the markup carries no `href`".

**Shadow — the impl region, verbatim.** The statements between `# impl-start` /
`# impl-end` copied unchanged (only the `Assert` and the `# type:` comments
removed), over a `PSeq`/`ToSeq` shim. The `pure` region is empty, so no `@Pure`
helper needs copying. The `@ContractOnly` `resolve_prefix` has no body to copy,
so it is bound to the REAL callee §3.1 axiomatizes — `django.urls.reverse`
(`django/urls/base.py:27`) — with `has_selector` becoming "pass `current_app=`"
vs "omit it", an empty selector lowering to `''`, and `NoReverseMatch` folding to
the EMPTY sequence (§2's carrier). The axiom is therefore exercised, not assumed.

**Type bridge (§2, inverted).** `cps(s) = [ord(c) for c in s]` / `uncps` invert
each other; generation happens on the concrete side (a registry of
`(instance name, mount, registered models)` triples) and is lowered per call.
`names[k]` ↔ that deployment's `AdminSite.name`; `prefixes[k]` ↔ `"/" + mount`;
`exposes[k]` ↔ whether deployment `k` carries a route for the target identifier
and this pk; `current_idx` ↔ the deployment rendering the page; `default_idx` ↔
the index whose prefix the real callee returns on the NO-SELECTOR path.

Two bridge values are OBSERVED from the real callee rather than re-implemented,
because both rules are subtler than they look:
  * `default_idx` — by calling `reverse` with no `current_app` (for an anchor
    identifier forced into EVERY deployment, so the observation always resolves)
    and locating the mount it lands in. The fallback rule is not unconditionally
    `app_dict['admin'][0]` (see §2's row), and an earlier version of this harness
    that assumed it mis-computed `default_idx` on registries containing a sibling
    named `admin`, producing spurious leg-B reports.
  * `exposes[k]` — by reversing the target identifier against a ONE-deployment
    URLconf carrying deployment `k`'s own route set, where no selection happens.
    An earlier version observed it through each deployment's own instance
    namespace, which silently mis-observes a COLON-named deployment (the view
    identifier is split on `:` too), again producing spurious leg-B reports.
Each deployment gets its own `build_patterns(model_keys)` object, so route sets
really do differ per sibling; a shared patterns object would make every sibling
carry identical routes and the whole route axis unobservable.

The registry is a real Django URLconf whose entries are the exact 3-tuple
`AdminSite.urls` returns — `(get_urls(), 'admin', self.name)` (`sites.py:303`) —
several sibling instance namespaces under one shared `admin` app namespace at
different mounts, with differing per-site registrations.

**Fidelity gates (the harness is checked, not trusted).** (0) patch applied;
(1) the lean 3-tuple URLconf + duck-typed receiver is observationally
**byte-identical** — same `app_dict` ordering and same returned markup — to a
URLconf built from real `admin.AdminSite(name=…)` objects driven through a real
`AdminReadonlyField` on a real `ModelAdmin`, over registry shapes that carry
DIFFERING per-site registrations of the real `User`/`Group`/`ContentType`
models, so the comparison covers the route axis and not only the selection axis;
(2) each `prefixes[current_idx]` is confirmed independently via the instance's
*own* namespace (`reverse('<name>:<view>')`, which never consults `current_app`),
guarded to the colon-free names for which that addressing is valid;
(3) mounts within a registry are pairwise non-prefix;
(4) coverage obligations — both selection branches, the discriminating
non-default-deployment case, the empty-identifier case, HETEROGENEOUS registries,
a current-deployment-lacks-route witness and a default-deployment-lacks-route
witness must each be exercised or the script fails.

**Two legs.** *Leg A* — shadow vs oracle (the href, or its absence, and the
shadow's URL re-wrapped with the repo's own `format_html` vs the oracle's full
markup). Since the impl region's only computation IS the `@ContractOnly` call,
Leg A is kept honest by an **anti-vacuity control** (precedent:
`django__django-12304`): three mutants — `has_selector=False` (= the pre-patch
call), "select with `names[default_idx]`", and "resolution is TOTAL: always
return `prefixes[current_idx]`" — must each be caught, or the script exits
non-zero as vacuous. *Leg B* — `model.py`'s guarded postcondition on `Result()`
checked against what the real patched code returns, read in the charitable
"carries that prefix" sense of refinement.md step 6: whichever of the FOUR
clauses the input's guards select is the one asserted, including the two that
demand NO link (`oracle_url is None`). All four are checked on every input; the
coverage obligations above fail the script if any of the four legs stops being
exercised.

**Input domain.** Every input satisfies the `Requires` *by construction*:
`len(names)==len(prefixes)==len(exposes)`, indices in range, names unique (the
`Forall2` precondition), every mount non-empty (the non-empty-prefix
precondition), and `names[current_idx]` U+003A-free (§3.1's domain restriction);
colon-bearing names are still generated as non-current siblings, which the
`Requires` permits. Boundary first: the exact F2P shape (`admin` +
`namespaced_admin` at the repo's own `test_admin/admin/` and
`test_admin/admin5/` mounts), singleton, the empty name as default and as
non-default, colon siblings, unicode / whitespace / digit /
app-namespace-colliding names, staircase route sets in which a sibling carries
an identifier the current deployment does not (and vice versa), targets no
deployment registers at all, and argument shapes the route converter rejects.

### Recorded verdict: **G-CONF = pass** (after two faithfulness repairs)

Leg A agrees on all 100000 inputs and all three mutants are caught (`prepatch`
43082, `default` 43077, `total` 100000), so the differential is not vacuous;
**Leg B reports 0 violations**. Coverage of the recorded run: resolving /
no-link branches of the real function 52417 / 47583; discriminating
non-default-deployment witnesses 33147; empty-identifier witnesses 5010;
heterogeneous registries 48602; current-deployment-lacks-route witnesses 23116;
default-deployment-lacks-route witnesses 564 (the row class that pins the
empty-identifier leg to the DEFAULT deployment's route table). The same counters
are in `meta.json`'s `G-CONF` stamp.

**Repair 1 — the empty instance identifier.** This gate previously reported
3026 leg-B violations, and that finding was real: when the current deployment's
`AdminSite.name` is the **empty string** and that deployment is not the
registered default, the real patched `get_admin_url` resolves against the
**default** deployment, not the current one, because `reverse` guards on
`if current_app:` (`django/urls/base.py:41`) and `''` is falsy. The then
unguarded `Ensures(Result() == ToSeq(prefixes)[current_idx])` was therefore
strictly stronger than the callee on a reachable, in-domain input (a zero-length
`PSeq` satisfies every `Requires`: the colon `Forall` is vacuous over it, and no
precondition demanded a non-empty name). Repaired by stating what the callee
guarantees, not by narrowing the domain (§3.1, "Falsiness dependency").

**Repair 2 — resolution is PARTIAL.** The spec then still modelled resolution as
TOTAL: it demanded a prefix on every admissible input. `reverse` narrows to one
instance FIRST and looks the identifier up only there (§3.1, "Partiality"), so
whenever the deployment resolution lands in does not carry a route for the
identifier the real composite renders NO link — and the spec demanded one. The
divergence class is "the requested view identifier does not resolve inside the
deployment resolution lands in", reachable through per-site `_registry`
asymmetry (the gold `test_patch`'s own starting state), through a target no site
registers, and through an argument the route's converter rejects. Repaired by
adding the `exposes` axis and the EMPTY-sequence carrier for "no link" (§2), and
by splitting each of the axiom's and the consumer's clauses in two. The repaired
model was measured against the real patched callee over a 650-observation
differential spread (13 registry shapes × 5 targets × 5 pk shapes): **0
disagreements**, with all four legs covered (named/route 164, named/no-route 411,
empty-identifier/route 16, empty-identifier/no-route 59) — including the row
that pins the empty-identifier leg to the DEFAULT deployment's route table
rather than the current one's (`cur='' tgt='auth.group' exposes=[True, False]`
⇒ the real page renders no link). The same spread against the UNPATCHED callee
disagrees on 116 of 650, so the added clauses discriminate rather than merely
accommodate.

**Two harness defects surfaced during the repairs, and both were in the bridge,
not the model.** (1) `build_registry` derived `default_idx` from
`app_dict['admin'][0]`, but `reverse` only falls back to `app_list[0]` in its
`elif ns not in app_list` arm, so on a registry containing a sibling named
`admin` the default is that sibling instead. (2) `observe_exposes` read each
deployment's route flag through that deployment's OWN instance namespace, which
is not addressable for a COLON-named deployment, so a colon-named default was
mis-observed as carrying no route. Both are now OBSERVED through selection-free
one-deployment probes (see the type bridge above). The F2P deployment names
(`admin`, `namespaced_admin`) are non-empty and colon-free and the F2P targets
are registered, so G-RESOLVE and the tested behaviour were never affected by
either.

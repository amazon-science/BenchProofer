#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13810 (nagini).

SHADOW: the impl region of model.py `assemble_chain`, copied verbatim below
with the contract calls (Requires/Ensures/Invariant) stripped. The @Pure
helpers are the specification-side fold and the deep-modelled token maps;
the impl inlines the token appends, so the shadow needs only the two token
constants. There are no @ContractOnly callees.

ORACLE: the REAL patched repo routine the model models per mapping.md —
``django.core.handlers.base.BaseHandler.load_middleware``. The gate applies
patch.diff to /testbed before this script runs; PYTHONPATH=/testbed makes
the patched module importable. The routine is driven end-to-end on a real
``BaseHandler`` over synthetic middleware classes (each combination of
sync/async capability and participate/decline). The two UNCHANGED
handler-deriving callees are wrapped with recording proxies that DELEGATE to
the originals, so the real control flow runs unmodified; the proxies only
annotate each derived handler object with its token trace per the mapping.md
bijection (adaptation -> [1, mode], wrapper construction -> [2], the initial
base handler -> []). The final running pair (handler, async-mode flag) is
read off the arguments of the top-of-stack adaptation call the routine makes
AFTER the walk — an unchanged boundary that receives exactly the loop's
final running state.

Type bridge (mapping.md section 2):
  * handler object identity <-> token trace (List[int]); traces are carried
    alongside the real objects by the recording proxies, keyed by object
    identity with the objects kept alive for the run.
  * bool flags <-> int in {0,1}.
  * target_mode[i] <-> the per-layer mode the real loop computes and passes
    to the adaptation callee; captured from the real call (the
    mode-selection logic is unchanged and abstracted as input data).
  * declines[i] <-> whether the i-th synthetic middleware class raises the
    layer-decline signal in its constructor (chosen by the generator).

Input domain: the model requires only two equal-length columns; every
generated (capabilities, declines) sequence with base_async in {0,1} is
Requires-satisfying. Boundary: all sequences of length <= 2 over the six
class kinds x both base modes, plus empty. Fuzz: random sequences of length
0..6 until >= 1e5 walks are checked. Pinned seed: 13810.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + django (the repo under test) only.
"""
import itertools
import json
import random
import sys
import types

SEED = 13810
N_TARGET = 100000

ADAPT_TOKEN = 1
WRAP_TOKEN = 2


# --- the impl region of model.py, verbatim, contract calls stripped ----------

def assemble_chain(target_mode, declines, base_async):
    handler = []  # type: List[int]
    handler_is_async = base_async
    i = 0
    while i < len(target_mode):
        # Tentatively adapt the current handler for this layer's target mode.
        adapted = handler + [ADAPT_TOKEN, target_mode[i]]  # type: List[int]
        if declines[i] == 1:
            # Layer declines: move on; the tentative adaptation is discarded so
            # the next layer inherits the unchanged running handler / flag.
            i = i + 1
            continue
        # Layer participates: commit the adapted+wrapped handler and advance the
        # running async-mode flag to this layer's target mode.
        handler = adapted + [WRAP_TOKEN]
        handler_is_async = target_mode[i]
        i = i + 1
    return handler, handler_is_async
    # impl-end


# --- real Django environment ---------------------------------------------------

def setup_django():
    from django.conf import settings
    settings.configure(
        DEBUG=False,
        MIDDLEWARE=[],
        ROOT_URLCONF=None,
        DATABASES={},
        INSTALLED_APPS=[],
        USE_TZ=False,
    )


def make_middleware_module():
    """Six synthetic middleware classes: capability combos x decline flag.
    Constructors capture the handler they are given; declining ones raise
    the layer-decline signal after capturing."""
    from django.core.exceptions import MiddlewareNotUsed

    mod = types.ModuleType("sbu_conf_mw")

    def make(name, can_sync, can_async, decline):
        def __init__(self, get_response):
            self._captured_handler = get_response
            if decline:
                raise MiddlewareNotUsed()

        def __call__(self, request):  # never invoked by chain assembly
            return None

        cls = type(name, (), {
            "sync_capable": can_sync,
            "async_capable": can_async,
            "__init__": __init__,
            "__call__": __call__,
            "__module__": "sbu_conf_mw",
        })
        setattr(mod, name, cls)
        return name

    kinds = []
    for can_sync, can_async, tag in [(True, False, "SyncOnly"),
                                     (False, True, "AsyncOnly"),
                                     (True, True, "Both")]:
        for decline in (False, True):
            name = "%s%s" % (tag, "Decline" if decline else "Ok")
            make(name, can_sync, can_async, decline)
            kinds.append(("sbu_conf_mw.%s" % name, decline))
    sys.modules["sbu_conf_mw"] = mod
    return kinds


def main():
    setup_django()
    from django.conf import settings
    from django.core.handlers import base as handlers_base
    from django.core.handlers.base import BaseHandler

    kinds = make_middleware_module()

    orig_convert = handlers_base.convert_exception_to_response
    orig_adapt = BaseHandler.adapt_method_mode

    class Recorder:
        """Per-run trace bookkeeping around the two unchanged callees."""

        def __init__(self):
            self.traces = {}       # id(handler object) -> trace tuple
            self.keepalive = []    # keeps derived objects alive (stable ids)
            self.layer_events = []  # (input_trace, mode, adapted_obj_id)
            self.top_call = None    # (final_trace, final_flag)
            self.pending = None

        def remember(self, obj, trace):
            self.traces[id(obj)] = trace
            self.keepalive.append(obj)

    rec_box = {"rec": None}

    def convert_proxy(get_response):
        result = orig_convert(get_response)  # the REAL unchanged callee
        rec = rec_box["rec"]
        if rec is not None:
            if hasattr(get_response, "_captured_handler"):
                # wrapper construction for a participating layer: the input
                # middleware instance holds the adapted handler it was given
                pend = rec.pending
                if pend is None or id(get_response._captured_handler) != pend[2]:
                    raise RuntimeError("wrapper input does not match the "
                                       "layer's adapted handler")
                input_trace, mode, _ = pend
                rec.remember(result,
                             input_trace + (ADAPT_TOKEN, mode, WRAP_TOKEN))
                rec.pending = None
            else:
                # initial base handler
                rec.remember(result, ())
        return result

    def adapt_proxy(self, is_async, method, method_is_async=None,
                    debug=False, name=None):
        rec = rec_box["rec"]
        if rec is not None and id(method) in rec.traces:
            trace = rec.traces[id(method)]
            result = orig_adapt(self, is_async, method, method_is_async,
                                debug=debug, name=name)
            # classify: in-loop tentative adaptation carries a name; the
            # top-of-stack call after the walk does not
            if name is not None:
                rec.pending = (trace, 1 if is_async else 0, id(result))
                rec.layer_events.append((1 if is_async else 0,))
                rec.keepalive.append(result)
            else:
                rec.top_call = (trace,
                                1 if method_is_async else 0)
            return result
        return orig_adapt(self, is_async, method, method_is_async,
                          debug=debug, name=name)

    handlers_base.convert_exception_to_response = convert_proxy
    BaseHandler.adapt_method_mode = adapt_proxy

    def run_real(spec, base_async):
        """spec: list of (dotted_path, decline) in VISIT order. Returns
        (final trace tuple, final flag int, captured target modes)."""
        settings.MIDDLEWARE = [path for path, _ in reversed(spec)]
        rec = Recorder()
        rec_box["rec"] = rec
        try:
            h = BaseHandler()
            h.load_middleware(is_async=bool(base_async))
        finally:
            rec_box["rec"] = None
        if rec.top_call is None:
            raise RuntimeError("top-of-stack adaptation was never observed")
        if len(rec.layer_events) != len(spec):
            raise RuntimeError("observed %d layer adaptations for %d layers"
                               % (len(rec.layer_events), len(spec)))
        modes = [ev[0] for ev in rec.layer_events]
        return rec.top_call[0], rec.top_call[1], modes

    def check(spec, base_async):
        declines = [1 if d else 0 for _, d in spec]
        try:
            real_trace, real_flag, modes = run_real(spec, base_async)
        except Exception as e:
            return ("DISAGREEMENT on (spec=%r base_async=%r):\n"
                    "  real walk raised %r" % (spec, base_async, e))
        shadow_trace, shadow_flag = assemble_chain(modes, declines,
                                                   base_async)
        if tuple(shadow_trace) != real_trace or shadow_flag != real_flag:
            return ("DISAGREEMENT on (spec=%r base_async=%r modes=%r):\n"
                    "  shadow (trace, flag) = (%r, %r)\n"
                    "  real   (trace, flag) = (%r, %r)"
                    % (spec, base_async, modes, shadow_trace, shadow_flag,
                       list(real_trace), real_flag))
        return None

    checked = 0

    # boundary: every sequence of length 0..2 over the six kinds, both modes
    for base_async in (0, 1):
        for n in (0, 1, 2):
            for combo in itertools.product(kinds, repeat=n):
                err = check(list(combo), base_async)
                if err:
                    print(err)
                    return 1
                checked += 1

    # fuzz to >= 1e5 total walks
    rng = random.Random(SEED)
    while checked < N_TARGET:
        n = rng.randint(0, 6)
        spec = [rng.choice(kinds) for _ in range(n)]
        base_async = rng.randint(0, 1)
        err = check(spec, base_async)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched chain assembly on "
          "%d walks (seed %d); 0 disagreements." % (checked, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())

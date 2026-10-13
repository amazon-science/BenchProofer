#!/usr/bin/env python3
"""G-AX executable soundness check for matplotlib__matplotlib-21568.

This bundle consumes NO `@ContractOnly` axiom: the math-mode neutralisation is
the operation under specification and is modelled DEEPLY as the per-code-point
fold `protected_seq` (model.py pure region). G-AX therefore validates that deep
model against the REAL changed string operation in `matplotlib.dates._wrap_in_tex`
(the gold post-patch behaviour), on boundary + randomized inputs.

The single kind-A check (A-reference):

  (A-reference) the deep model `protected_seq` (model.py pure region) == the
      changed per-code-point protection the gold `_wrap_in_tex` performs:
        '-'(45) -> '{-}'   '{' '-' '}'   = [123, 45, 125]
        ':'(58) -> '{:}'   '{' ':' '}'   = [123, 58, 125]
        ' '(32) -> '\\;'   '\\' ';'      = [92, 59]
        else identity (singleton)

The real `_wrap_in_tex` also performs an UNCHANGED regex wrapping of alphabetic
runs and an UNCHANGED `$\\mathdefault{...}$` framing + empty-fragment removal;
those are the I/R framing of refinement.md and are NOT under specification. The
protection chain operates on the post-regex string, but the regex only ever
introduces the framing characters  } $ \\ m a t h d e f a u l t {  — none of
which is '-' ':' or ' ' — so the set of protected code points it acts on is
exactly the protected code points of the original text. Hence we validate the
deep model directly against the gold `.replace` chain (the changed operation),
which is the substitution `protected_seq` encodes, and additionally confirm the
end-to-end gold `_wrap_in_tex` agrees with model+framing on the F2P-shaped
labels.

Imports nothing repo-specific beyond the standard-library `re` (the very module
the function uses). Exit 0 iff every obligation holds.
"""
import re
import random
import sys

# --- model.py reference encodings (kept in lock-step with the pure region) ---

_PROTECT = {
    45: [123, 45, 125],   # '-'  -> '{-}'
    58: [123, 58, 125],   # ':'  -> '{:}'
    32: [92, 59],         # ' '  -> '\;'
}


def protected_seq(codepoints):
    """Reference implementation of model.py's deep model `protected_seq`, as a
    list of code points (the per-code-point protection substitution)."""
    out = []
    for c in codepoints:
        out.extend(_PROTECT.get(c, [c]))
    return out


# --- the REAL changed operation (gold _wrap_in_tex's .replace chain) ---------

def real_protect_chain(s):
    """The exact changed string operation from the gold patch (the per-code-point
    protection), in isolation:
        ret_text.replace('-', '{-}').replace(':', '{:}').replace(' ', r'\\;')
    """
    return s.replace('-', '{-}').replace(':', '{:}').replace(' ', r'\;')


# --- the REAL end-to-end gold function (verbatim from the post-patch source) --

def real_wrap_in_tex(text):
    p = r'([a-zA-Z]+)'
    ret_text = re.sub(p, r'}$\1$\\mathdefault{', text)
    # Braces ensure symbols are not spaced like binary operators.
    ret_text = ret_text.replace('-', '{-}').replace(':', '{:}')
    # To not concatenate space between numbers.
    ret_text = ret_text.replace(' ', r'\;')
    ret_text = '$\\mathdefault{' + ret_text + '}$'
    ret_text = ret_text.replace('$\\mathdefault{}$', '')
    return ret_text


# --- the model-side framing (R/I framing of refinement.md) -------------------

def model_wrap_via_deep_model(text):
    """Build the same framing as the real function, but compute the protection
    via the deep model `protected_seq` instead of the `.replace` chain. Used to
    confirm protection is the ONLY behavioural delta and the deep model produces
    the gold output once the unchanged framing is applied."""
    p = r'([a-zA-Z]+)'
    ret_text = re.sub(p, r'}$\1$\\mathdefault{', text)
    protected = "".join(chr(c) for c in protected_seq([ord(ch) for ch in ret_text]))
    ret_text = '$\\mathdefault{' + protected + '}$'
    ret_text = ret_text.replace('$\\mathdefault{}$', '')
    return ret_text


# --- the checks --------------------------------------------------------------

def check_protect_reference(s):
    """Assert the deep model protected_seq(s) == the REAL changed protection."""
    observed = [ord(ch) for ch in real_protect_chain(s)]      # real changed op
    expected = protected_seq([ord(ch) for ch in s])           # deep model
    assert observed == expected, (
        "protected_seq deep model unsound on %r: real .replace chain gave %r, "
        "deep model gives %r" % (s, observed, expected))


def check_end_to_end(text):
    """Assert the gold _wrap_in_tex equals the deep-model-driven framing, i.e.
    protection is the only behavioural difference and the deep model + unchanged
    framing reproduce the gold output exactly."""
    assert real_wrap_in_tex(text) == model_wrap_via_deep_model(text), (
        "end-to-end mismatch on %r: gold=%r model-via-deep=%r"
        % (text, real_wrap_in_tex(text), model_wrap_via_deep_model(text)))


def main():
    significant = ['-', ':', ' ']
    ordinary = ['0', '1', '2', '5', '9', '.', 'a', 'J', 'n', 'e', 'b',
                'F', 'M', 'd', 'y', '{', '}', '$', '\\', 'x']

    # --- protected_seq deep model (A-reference): boundary cases -----------
    boundary = [""]
    boundary += significant                       # each protected char alone
    boundary += [c + c for c in significant]      # doubled
    boundary += ["".join(significant)]            # all three together
    boundary += ["".join(reversed(significant))]
    # mixtures with ordinary text and the F2P-shaped labels
    boundary += [
        "1990",
        "1990-01-01",
        "01-01 00",
        "01 00:00",
        "00:00:00",
        "04:00",
        "59.5",
        "Jan-01",
        "Jan 01 1990",
        "Jan",
        "01-01 12",
        "1990{-}01",       # pre-protected braces must not be re-protected
        "a-b:c d",
        "-:- :- ",
        ":::",
        "   ",
        "---",
    ]
    for s in boundary:
        check_protect_reference(s)

    # --- protected_seq deep model (A-reference): randomized fuzz ----------
    rng = random.Random(21568)
    alphabet = significant + ordinary
    for _ in range(20000):
        n = rng.randint(0, 24)
        s = "".join(rng.choice(alphabet) for _ in range(n))
        check_protect_reference(s)

    # --- end-to-end: deep model + unchanged framing == gold _wrap_in_tex --
    e2e = boundary + [
        "Jan 01 1990", "01-01 00", "01 00:00", "04:00", "00:00:00",
        "16:00", "20:00", "59.5", "00.5", "01.0", "1990-01-31",
    ]
    for t in e2e:
        check_end_to_end(t)
    for _ in range(5000):
        n = rng.randint(0, 16)
        # include letters so the regex framing is exercised
        s = "".join(rng.choice(alphabet + ['A', 'b', 'C', 'z']) for _ in range(n))
        check_end_to_end(s)

    print("G-AX OK: protected_seq deep model (== gold _wrap_in_tex protection) "
          "sound on %d boundary + 20000 fuzz protection inputs; end-to-end "
          "deep-model framing == gold on %d boundary + 5000 fuzz labels"
          % (len(boundary), len(e2e)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

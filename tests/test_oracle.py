"""CI tests: oracle conventions and solver claims, validated numerically."""
from sympy import S
from sympy.physics.wigner import wigner_6j, wigner_9j

from yutsis.oracle import ClosedDiagram, k33, prism, tetrahedron, theta


def close(a, b, tol=1e-9):
    return abs(a - b) < tol

def test_theta_normalization():
    # theta = (-1)^(j1+j2+j3) in this orientation (odd-permutation node sign)
    assert close(theta(1, 1, 1).value(), -1.0)
    assert close(theta(S(1)/2, S(1)/2, 1).value(), 1.0)
    assert close(theta(1, 1, 3).value(), 0.0)

def test_tetrahedron_is_6j_phase_exact():
    for js in [(1,1,1,1,1,1), (1,1,2,1,1,2),
               (S(1)/2,S(1)/2,1,S(1)/2,S(1)/2,1),
               (S(3)/2,1,S(1)/2,1,S(3)/2,1)]:
        assert close(tetrahedron(*js).value(), float(wigner_6j(*js)))

def test_k33_is_9j_phase_exact():
    for js in [(1,1,2,1,1,2,2,2,2),
               (S(1)/2,S(1)/2,1,S(1)/2,S(1)/2,1,1,1,2),
               (1,S(3)/2,S(1)/2,S(3)/2,1,S(1)/2,S(1)/2,S(1)/2,1)]:
        assert close(k33(*js).value(), float(wigner_9j(*js)))

def test_self_loop_forces_j_zero_and_weighs_sqrt_2k_plus_1():
    """The k=1 sector, at oracle level.

    Closing two legs of a vertex forces its third edge to zero:
        sum_m (-1)^(k-m) 3j(k k jc; m -m mc) = sqrt(2k+1) d(jc,0) d(mc,0)
    so the dumbbell (two tadpoles joined by a bridge) evaluates to
    sqrt(2k+1)*sqrt(2f+1) at jc = 0, and vanishes otherwise.

    Before the slot-order fix the oracle scored both loop slots as tails
    and returned 0.0 here -- it could not express the sector at all."""
    import math
    for k in (S(1)/2, S(1), S(3)/2):
        for f in (S(1)/2, S(1)):
            cd = ClosedDiagram({"k": ("v", "v", k), "c": ("v", "w", S(0)),
                                "f": ("w", "w", f)},
                               {"v": ("k", "k", "c"), "w": ("c", "f", "f")})
            want = math.sqrt(2 * float(k) + 1) * math.sqrt(2 * float(f) + 1)
            assert close(cd.value(), want)


def test_self_loop_diagram_vanishes_off_j_zero():
    cd = ClosedDiagram({"k": ("v", "v", S(1)/2), "c": ("v", "w", S(1)),
                        "f": ("w", "w", S(1)/2)},
                       {"v": ("k", "k", "c"), "w": ("c", "f", "f")})
    assert close(cd.value(), 0.0)


def test_prism_factorizes_up_to_phase():
    v = prism(1,1,1, 1,1,1, 1,1,1).value()
    p = float(wigner_6j(1,1,1,1,1,1))**2
    assert close(abs(v), abs(p))   # magnitude exact; sign is milestone-2 phase

if __name__ == "__main__":
    test_theta_normalization()
    test_tetrahedron_is_6j_phase_exact()
    test_k33_is_9j_phase_exact()
    test_prism_factorizes_up_to_phase()
    print("all oracle tests pass")

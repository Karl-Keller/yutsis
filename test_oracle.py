"""CI tests: oracle conventions and solver claims, validated numerically."""
from sympy import S
from sympy.physics.wigner import wigner_6j, wigner_9j
from oracle import theta, tetrahedron, prism, k33

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

def test_prism_factorizes_up_to_phase():
    v = prism(1,1,1, 1,1,1, 1,1,1).value()
    p = float(wigner_6j(1,1,1,1,1,1))**2
    assert close(abs(v), abs(p))   # magnitude exact; sign is milestone-2 phase

if __name__ == "__main__":
    test_theta_normalization(); test_tetrahedron_is_6j_phase_exact()
    test_k33_is_9j_phase_exact(); test_prism_factorizes_up_to_phase()
    print("all oracle tests pass")

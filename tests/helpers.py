"""Small numeric helpers shared by the test suite.

Deliberately dependency-free: the tests must not need numpy to check a
3x3 gate composition, and keeping these here stops each test file from
growing its own copy.
"""


def matmul(a, b):
    """Plain matrix product of two nested-list matrices."""
    return [[sum(a[i][k] * b[k][j] for k in range(len(b)))
             for j in range(len(b[0]))]
            for i in range(len(a))]


def max_abs_diff(a, b):
    """Largest elementwise |a - b| over two equally shaped matrices."""
    return max(abs(a[i][j] - b[i][j])
               for i in range(len(a)) for j in range(len(a[0])))


def gram(a):
    """a^T a -- used to check unitarity of a real gate block."""
    n = len(a)
    return [[sum(a[k][i] * a[k][j] for k in range(n)) for j in range(n)]
            for i in range(n)]


def identity(n):
    return [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]

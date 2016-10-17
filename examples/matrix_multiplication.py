from .. import tracker, memory

zero_8 = [0] * 8


class FakeMatrix(object):
    def __init__(self, base, R, C):
        self.base = base
        self.R = R
        self.C = C

    def get(self, i, j):
        addr = self.base + i * self.C + j
        return memory.read(addr, 8)

    def set(self, i, j):
        addr = self.base + i * self.C + j
        return memory.write(addr, zero_8)


def mul1(A, B, O):
    assert A.C == B.R
    assert O.R == A.R and O.C == B.C

    for i in range(A.R):
        for j in range(B.C):
            for k in range(A.C):
                A.get(i, k)
                B.get(k, j)
         #       O.set(i, j)


def mul2(A, B, O):
    B2 = FakeMatrix(10**8, B.R, B.C)
    for i in range(B.R):
        for j in range(B.C):
            B.get(j, i)
            B2.set(i, j)

    for i in range(A.R):
        for j in range(B.C):
            for k in range(A.C):
                A.get(i, k)
                B.get(j, k)
                #O.set(i, j)


if __name__ == '__main__':

    # 'allocate' 3 2d matrices
    N = 500
    A = FakeMatrix(0, N, N)
    B = FakeMatrix(10**7, N, N)
    O = FakeMatrix(2 * 10**7, N, N)

    tracker.clear()
    mul1(A, B, O)
    print(tracker.get_num_cycles(), tracker.sources)

    tracker.clear()

    mul2(A, B, O)
    print(tracker.get_num_cycles(), tracker.sources)

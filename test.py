import pymemsim
from pymemsim import Store


class TestStore(object):
    def setup(self):
        self.t = pymemsim.Tracker()

    def get_many_stores(self):
        return [
            # fully associative, write through, no backing
            Store('test', 1, 2, 1, tracker=self.t),

            # 2-set associative, write through, with no backing
            Store('test', 2, 2, 1, assoc=2, tracker=self.t),
        ]

    def test_read_write(self):
        for s in self.get_many_stores():
            s.write(0, [1, 2])
            assert 1 == s.read(0, 1)
            assert 2 == s.read(1, 1)
            assert [1, 2] == s.read(0, 2)

    def test_cost_infinite(self):
        cost = 3
        verify = self._assert_cost

        # store with infinite storage
        s = Store('infinite', None, 64, cost, tracker=self.t)

        # initially tracker has no cycles
        assert 0 == self.t.get_num_cycles()

        # read some data, should be zerod out
        assert 0 == s.read(0, 1)

        # cost should be that of a single lookup
        verify(cost)

        # reading the same thing again is the same
        assert 0 == s.read(0, 1)
        verify(cost)

        # twice for 2 blocks
        assert [0] * 2 * s.block_size == s.read(0, 2*s.block_size)
        verify(2*cost)

        # modifying a block is twice the cost
        s.write(124, [1, 2])
        verify(2*cost)

    def test_small_infinite_cost(self):
        verify = self._assert_cost
        cost1, cost2 = 3, 7
        # infinite storage
        s2 = Store('infinite', None, 64, cost2, tracker=self.t)

        # small store of 2 blocks, each block being 2 bytes
        s1 = Store('small', 2, 2, cost1, next_store=s2, tracker=self.t)

        # initially tracker has no cycles
        assert 0 == self.t.get_num_cycles()

        # read some data, should be zerod out
        # cost: one level 1 miss + one level 2 hit + one level 1 write
        assert 0 == s1.read(0, 1)
        verify(2*cost1 + cost2)

        # now read the same thing again, and it should be in level 1 cache
        assert 0 == s1.read(0, 1)
        verify(cost1)

        # now read the next block
        # cost: miss in level 1, hit in level 2, write in level 1
        assert 0 == s1.read(2, 1)
        verify(2*cost1 + cost2)

        # read one more block, should cause original block to get evicted
        # cost: miss in l1, hit in l2, write in l1
        assert 0 == s1.read(4, 1)
        verify(2*cost1 + cost2)

        # read original block
        # cost: miss in l1 (due to previous eviction), hit in l2, write in l1
        assert 0 == s1.read(0, 1)
        verify(2*cost1 + cost2)

        # modifying a block present in both l1 and l2
        # cost: read in level 1, modify in level 1, read in l2, write in level 2
        s1.write(0, [1, 2])
        verify(2*cost1 + 2*cost2)

        # modifying a block that is only in level 2
        # cost: miss in level 1, hit in level 2, copy to level 1, modify in l1, read in
        # level 2, write in
        # level 2
        s1.write(2, [1, 2])
        verify(3*cost1 + 3*cost2)

    def _assert_cost(self, expected):
        actual = self.t.get_num_cycles()
        assert expected == actual, 'Expected %d but got %d. Full sequence %s' % (expected, actual, self.t.events)
        self.t.clear()

#!/usr/bin/python

import unittest
import stats

class RandomVariableStat(unittest.TestCase):
    def test_simple(self):
        d = stats.MeanVarStat()
        # prior says 1 2p win, 1 2p loss  # freq = 2, sum = 2, sum_sq = 4
        d.add_outcome(2)                  # freq = 3, sum = 4, sum_sq = 8
        d.add_outcome(3)                  # freq = 4, sum = 7, sum_sq = 17
        self.assertEquals(d.real_frequency(), 2)
        self.assertEquals(d.frequency(), 4)
        self.assertEquals(d.mean(), 7. / 4)
        self.assertEquals(d.variance(), (17 - 49. / 4) / 3) 

    def test_merge(self):
        a = stats.MeanVarStat()
        b = stats.MeanVarStat()

        a.add_outcome(1)
        b.add_outcome(1)
        
        b.merge(a)

        self.assertEquals(b.real_frequency(), 2)


if __name__ == '__main__':
    unittest.main()

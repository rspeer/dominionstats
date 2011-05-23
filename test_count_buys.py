#!/usr/bin/python
# -*- coding: utf-8 -*-
try:
    import unittest2 as unittest
except ImportError, e:
    import unittest

import count_buys

class TestBuyStats(unittest.TestCase):
    def test_merge_buy_stat(self):
        a = count_buys.BuyStat()
        b = count_buys.BuyStat()

        a.available.add_outcome(1)
        b.available.add_outcome(3)
        self.assertEquals(a.available.frequency(), 1)
        self.assertEquals(b.available.frequency(), 1)

        b.merge(a)

        self.assertEquals(b.available.frequency(), 2)

    def test_merge_deck_buy_stats(self):
        a = count_buys.DeckBuyStats()
        b = count_buys.DeckBuyStats()

        a['Estate'].available.add_outcome(2)
        b['Estate'].available.add_outcome(0)

        self.assertEquals(a['Estate'].available.frequency(), 1)
        self.assertEquals(b['Estate'].available.frequency(), 1)
        b.merge(a)
        self.assertEquals(b['Estate'].available.frequency(), 2)

if __name__ == '__main__':
    unittest.main()

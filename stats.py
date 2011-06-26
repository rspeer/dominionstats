#!/usr/bin/python
# -*- coding: utf-8 -*-

""" The stats mdoule contains two objects for tracking distributions.

The MeanVarStat keeps a running total of frequence, mean, and variance of
a random variable.

DiffStat supports finding the difference between two MeanVarStat objects.
"""

import math

import primitive_util
import mergeable

class MeanVarStat(primitive_util.PrimitiveConversion, 
                  mergeable.MergeableObject):
    __slots__ = ('freq', 'sum', 'sum_sq', 'pfreq', 'psum', 'psum_sq')
    
    def __init__(self, prior_freq=2.0, prior_sum=2.0, prior_sum_sq=4.0):
        self.freq = prior_freq
        self.sum = prior_sum
        self.sum_sq = prior_sum_sq
        self.pfreq = prior_freq
        self.psum = prior_sum
        self.psum_sq = prior_sum_sq

    def add_outcome(self, val):
        self.freq += 1
        self.sum += val
        self.sum_sq += val * val

    def real_frequency(self):
        return self.freq - self.pfreq

    def frequency(self):
        return self.freq

    def mean(self):
        return self.sum / self.freq

    def variance(self):
        if self.freq <= 1:
            return 1e10
        return (((self.sum_sq) - ((self.sum) ** 2) / (self.freq)) /
                (self.freq - 1))

    def std_dev(self):
        return self.variance() ** .5
 
    def sample_std_dev(self):
        return (self.variance() / (self.freq or 1)) ** .5

    def __add__(self, o):
        self._assert_priors_match(o)
        ret = MeanVarStat()
        ret.freq = self.freq + o.freq - o.pfreq
        ret.sum = self.sum + o.sum - o.psum
        ret.sum_sq = self.sum_sq + o.sum_sq - o.psum_sq
        return ret
    
    def __sub__(self, o):
        self._assert_priors_match(o)
        ret = MeanVarStat()
        ret.freq = self.freq - o.freq + o.pfreq
        ret.sum = self.sum - o.sum + o.psum
        ret.sum_sq = self.sum_sq - o.sum_sq + o.psum_sq
        return ret

    def mean_diff(self, o):
        return DiffStat(self, o)

    def render_interval(self, factor=2, sig_digits=2):
        if self.sample_std_dev() >= 10000:
            return u'-'
        return u'%.2f ± %.2f' % (self.mean(), factor * self.sample_std_dev())

    def __eq__(self, o):
        assert type(o) == MeanVarStat
        return (self.freq == o.freq and 
                self.sum == o.sum and
                self.sum_sq == o.sum_sq)

    def to_primitive_object(self):
        return [self.freq, self.sum, self.sum_sq]

    def from_primitive_object(self, obj):
        if type(obj) == list:
            self.freq, self.sum, self.sum_sq = obj
        elif type(obj) == dict:
            self.__dict__ = obj
        else:
            assert 'Confused by obj %s' % str(obj) and False

    def _assert_priors_match(self, obj):
        assert self.pfreq == obj.pfreq
        assert self.psum == obj.psum
        assert self.psum_sq == obj.psum_sq

    def merge(self, obj):
        self._assert_priors_match(obj)
        self.freq += obj.freq - obj.pfreq
        self.sum += obj.sum - obj.psum
        self.sum_sq += obj.sum_sq - obj.psum_sq

    def __str__(self):
        return '%s, %s, %s' % (self.freq, self.sum, self.sum_sq)

class DiffStat(object):
    """
    Statistics about the difference in means of two distributions.
    """
    def __init__(self, mvs1, mvs2):
        self.mvs1 = mvs1
        self.mvs2 = mvs2

    @property
    def freq(self):
        return self.mvs1.freq

    def render_interval(self, factor=2, sig_digits=2):
        if self.sample_std_dev() >= 10000:
            return u'-'
        return u'%.2f ± %.2f' % (self.mean(), factor * self.sample_std_dev())
        
    def render_std_devs(self):
        if not self.freq:
            return u'-'
        return u'%.2f' % (self.mean() / self.sample_std_dev())

    def mean(self):
        return self.mvs1.mean() - self.mvs2.mean()

    def sample_std_dev(self):
        return math.hypot(self.mvs1.sample_std_dev(), 
                          self.mvs2.sample_std_dev())

    def mean_diff(self, o):
        return DiffStat(self, o)


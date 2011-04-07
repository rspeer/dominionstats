#!/usr/bin/python
# -*- coding: utf-8 -*-

""" Do lexical analysis turns. """

import ply.lex
import re

import card_info

tokens = (
    'NEWLINE',
    'CARD',
    'PLAYER',
    'NUMBER',
    'TRASHING',
    'TRASHES',
    'IS_TRASHED',
    'GAINING',
    'PLAYS',
    'BUYS',
    'GAINS', 
    'TOKEN',
    'DISCARDS',
    'REVEALS',
    'RETURNING',
    'REVEALING',
    'TO_THE_SUPPLY',
    'GETTING',
    'WHICH_IS_WORTH',
    'TURNS_UP_A',
    'REVEALS_A',
    'REPLACING',
    'WITH_A',
    'TRASHES_IT',
)

t_NEWLINE = r'\n'

def t_CARD(t):
    '<span[^>]*>(?P<card_name>[^<]*)</span>'
    maybe_plural = t.lexer.lexmatch.group('card_name')
    t.value = card_info.SingularOf(maybe_plural)
    return t

def t_PLAYER(t):
    'player(?P<num>\d)'
    t.value = int(t.lexer.lexmatch.group('num'))
    return t

def t_NUMBER(t):
    '\d+'
    t.value = int(t.value)
    return t

for tok in tokens:
    if not 't_' + tok in locals():
        locals()['t_' + tok] = tok.lower().replace('_', ' ')

def t_error(t):
    """ Skip single character input on error, let's us ignore boring text """
    t.lexer.skip(1)

lexer = ply.lex.lex()

def iso_lex(turn_str):
    """ Given a turns string, return a list of ply tokens. """
    ret = []
    lexer.input(turn_str)
    # Tokenize
    while True:
        tok = lexer.token()
        if not tok: break # No more input
        ret.append(tok)
    return ret

def type_lex(turn_str):
    """ Like iso_lex, but return only a list of token types. """
    ret = []
    for tok in iso_lex(token_list):
        ret.append(tok.type)
    return ret

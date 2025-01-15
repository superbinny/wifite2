#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ..util.color_win import Color
from .result_win import CrackResult


class CrackResultBruteForce(CrackResult):
    def __init__(self, bssid, essid, ascii_key):
        self.result_type = 'BruteForce'
        self.bssid = bssid
        self.essid = essid
        # self.hex_key = hex_key
        self.ascii_key = ascii_key
        super(CrackResultBruteForce, self).__init__()

    def dump(self):
        if self.essid:
            Color.pl('{+}      ESSID: {C}%s{W}' % self.essid)
        Color.pl('{+}      BSSID: {C}%s{W}' % self.bssid)
        Color.pl('{+} Encryption: {C}%s{W}' % self.result_type)
        # Color.pl('{+}    Hex Key: {G}%s{W}' % self.hex_key)
        if self.ascii_key:
            Color.pl('{+}  Ascii Key: {G}%s{W}' % self.ascii_key)

    def print_single_line(self, longest_essid):
        self.print_single_line_prefix(longest_essid)
        Color.p('{G}%s{W}' % 'WEP'.ljust(5))
        Color.p('  ')
        # Color.p('Hex: {G}%s{W}' % self.hex_key.replace(':', ''))
        if self.ascii_key:
            Color.p(' (ASCII: {G}%s{W})' % self.ascii_key)
        Color.pl('')

    def to_dict(self):
        return {
            'type': self.result_type,
            'date': self.date,
            'essid': self.essid,
            'bssid': self.bssid,
            # 'hex_key': self.hex_key,
            'ascii_key': self.ascii_key
        }


if __name__ == '__main__':
    crw = CrackResultBruteForce('AA:BB:CC:DD:EE:FF', 'Test Router', 'abcde')
    crw.dump()
    crw.save()

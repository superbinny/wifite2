#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .dependency_win import Dependency
from ..config_win import Configuration
from ..util.color_win import Color
from ..util.process_win import Process


class Cowpatty(Dependency):
    """ Wrapper for Cowpatty program. """
    dependency_required = False
    dependency_name = 'cowpatty'
    dependency_url = 'https://tools.kali.org/wireless-attacks/cowpatty'

    @staticmethod
    def crack_handshake(handshake, show_command=False):
        # Crack john file
        command = [
            'cowpatty',
            '-f', Configuration.wordlist,
            '-r', handshake.capfile,
            '-s', handshake.essid
        ]
        if show_command:
            Color.pl('{+} {D}Running: {W}{P}%s{W}' % ' '.join(command))
        process = Process(command)
        stdout, stderr = process.get_output()

        key = None
        for line in stdout.split('\n'):
            if 'The PSK is "' in line:
                key = line.split('"', 1)[1][:-2]
                break

        return key

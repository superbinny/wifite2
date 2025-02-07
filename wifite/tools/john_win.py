#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .dependency_win import Dependency
from ..config_win import Configuration
from ..util.color_win import Color
from ..util.process_win import Process
from ..tools.hashcat_win import HcxPcapngTool

# import os


class John(Dependency):
    """ Wrapper for John program. """
    dependency_required = False
    dependency_name = 'john'
    dependency_url = 'https://www.openwall.com/john/'

    @staticmethod
    def crack_handshake(handshake, show_command=False):
        john_file = HcxPcapngTool.generate_john_file(handshake, show_command=show_command)

        key = None
        # Use `john --list=formats` to find if OpenCL or CUDA is supported.
        formats_stdout = Process(['john', '--list=formats']).stdout()
        if 'wpapsk-opencl' in formats_stdout:
            john_format = 'wpapsk-opencl'
        elif 'wpapsk-cuda' in formats_stdout:
            john_format = 'wpapsk-cuda'
        else:
            john_format = 'wpapsk'

        # Crack john file
        command = ['john', f'--format={john_format}', f'--wordlist={Configuration.wordlist}', john_file]
        if show_command:
            Color.pl('{+} {D}Running: {W}{P}%s{W}' % ' '.join(command))
        process = Process(command)
        process.wait()

        # Run again with --show to consistently get the password
        command = ['john', '--show', john_file]
        if show_command:
            Color.pl('{+} {D}Running: {W}{P}%s{W}' % ' '.join(command))
        process = Process(command)
        stdout, stderr = process.get_output()

        # Parse password (regex doesn't work for some reason)
        if '0 password hashes cracked' in stdout:
            key = None
        else:
            for line in stdout.split('\n'):
                if handshake.capfile in line:
                    key = line.split(':')[1]
                    break

        if Configuration.linux.exists(john_file):
            Configuration.linux.remove(john_file)

        return key

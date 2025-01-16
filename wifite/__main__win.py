#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from .config_win import Configuration
except (ValueError, ImportError) as e:
    raise Exception("You may need to run wifite from the root directory (which includes README.md)", e) from e


from .util.color_win import Color
import gevent

# import os
# import subprocess

class Wifite(object):

    def __init__(self):
        """
        Initializes Wifite.
        Checks that its running under *nix, with root permissions and ensures dependencies are installed.
        """        
        self.print_banner()

        Configuration.initialize(load_interface=False)
        if Configuration.linux.name == 'nt':
            Color.pl('{!} {R}error: {O}wifite{R} must be run under a {O}*NIX{W}{R} like OS')
            Configuration.exit_gracefully()
        uid = Configuration.linux.getuid()
        while uid is None:
            uid = Configuration.linux.getuid()
            gevent.sleep(0.2)

        if uid != 0:
            Color.pl('{!} {R}error: {O}wifite{R} must be run as {O}root{W}')
            Color.pl('{!} {R}re-run with {O}sudo{W}')
            Configuration.exit_gracefully()

        from .tools.dependency_win import Dependency
        Dependency.run_dependency_check()

    def start(self):
        """
        Starts target-scan + attack loop, or launches utilities depending on user input.
        """
        from .model.result_win import CrackResult
        from .model.handshake_win import Handshake
        from .util.crack_win import CrackHelper

        if Configuration.show_cracked:
            CrackResult.display('cracked')

        elif Configuration.show_ignored:
            CrackResult.display('ignored')

        elif Configuration.check_handshake:
            Handshake.check()

        elif Configuration.crack_handshake:
            CrackHelper.run()

        else:
            Configuration.get_monitor_mode_interface()
            self.scan_and_attack()

    # @staticmethod
    def print_banner(self):
        """Displays ASCII art of the highest caliber."""
        Color.pl(r' {G}  .     {GR}{D}     {W}{G}     .    {W}')
        Color.pl(r' {G}.´  ·  .{GR}{D}     {W}{G}.  ·  `.  {G}wifite2 {D}%s{W}' % Configuration.version)
        Color.pl(r' {G}:  :  : {GR}{D} (¯) {W}{G} :  :  :  {W}{D}a wireless auditor by derv82{W}')
        Color.pl(r' {G}`.  ·  `{GR}{D} /¯\ {W}{G}´  ·  .´  {W}{D}maintained by kimocoder, modify by Binny{W}')
        Color.pl(r' {G}  `     {GR}{D}/¯¯¯\{W}{G}     ´    {C}{D}https://github.com/superbinny/wifite2{W}')
        Color.pl('')

    # @staticmethod
    def scan_and_attack(self):
        """
        1) Scans for targets, asks user to select targets
        2) Attacks each target
        """
        from .util.scanner_win import Scanner
        from .attack.all_win import AttackAll

        Color.pl('')

        # Scan
        s = Scanner()
        do_continue = s.find_targets()
        targets = s.select_targets()

        if Configuration.infinite_mode:
            while do_continue:
                AttackAll.attack_multiple(targets)
                do_continue = s.update_targets()
                if not do_continue:
                    break
                targets = s.select_targets()
            attacked_targets = s.get_num_attacked()
        else:
            # Attack
            attacked_targets = AttackAll.attack_multiple(targets)

        Color.pl('{+} Finished attacking {C}%d{W} target(s), exiting' % attacked_targets)


def entry_point():
    try:
        wifite = Wifite()
        wifite.start()
    except Exception as e2:
        Color.pexception(e2, call_from='entry_point')
        Color.pl('\n{!} {R}Exiting{W}\n')

    except KeyboardInterrupt:
        Color.pl('\n{!} {O}Interrupted, Shutting down...{W}')

    # Delete Reaver .pcap
    ## subprocess.run(["rm", "reaver_output.pcap"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    ## Configuration.exit_gracefully()


if __name__ == '__main__':
    # init_linux(server_ip='192.168.192.130', server_port='12999')
    entry_point()

#!/usr/bin/env python
# -*- coding: utf-8 -*-

#from wifite.tools.aircrack_win import Aircrack
#from wifite.tools.bully_win import Bully
#from wifite.tools.hashcat_win import Hashcat, HcxDumpTool, HcxPcapngTool
#from wifite.tools.ip_win import Ip
#from wifite.tools.iw_win import Iw
#from wifite.tools.macchanger_win import Macchanger
#from wifite.tools.reaver_win import Reaver
#from wifite.tools.tshark_win import Tshark


class Dependency(object):
    dependency_name = None
    dependency_required = None
    dependency_url = None
    required_attr_names = ['dependency_name', 'dependency_url', 'dependency_required']

    # https://stackoverflow.com/a/49024227
    def __init_subclass__(cls):
        for attr_name in cls.required_attr_names:
            if attr_name not in cls.__dict__:
                raise NotImplementedError(f'Attribute "{attr_name}" has not been overridden in class "{cls.__name__}"')

    @classmethod
    def exists(cls):
        from ..util.process_win import Process
        return Process.exists(cls.dependency_name)

    @classmethod
    def run_dependency_check(cls):
        from ..util.color_win import Color
        from .aircrack_win import Aircrack
        from .ip_win import Ip
        from .iw_win import Iw
        from .bully_win import Bully
        from .reaver_win import Reaver
        from .tshark_win import Tshark
        from .macchanger_win import Macchanger
        from .hashcat_win import Hashcat, HcxDumpTool, HcxPcapngTool

        apps = [
            # Aircrack
            Aircrack,  # Airodump, Airmon, Aireplay,
            # wireless/net tools
            Iw, Ip,
            # WPS
            Reaver, Bully,
            # Cracking/handshakes
            Tshark,
            # Hashcat
            Hashcat, HcxDumpTool, HcxPcapngTool,
            # Misc
            Macchanger
        ]

        missing_required = any(app.fails_dependency_check() for app in apps)

        if missing_required:
            Color.pl('{!} {O}At least 1 Required app is missing. Wifite needs Required apps to run{W}')
            import sys
            sys.exit(-1)

    @classmethod
    def fails_dependency_check(cls):
        from ..util.color_win import Color
        from ..util.process_win import Process

        # print(f'Check {cls.dependency_name} ...')
        if Process.exists(cls.dependency_name):
            return False
        
        # print(f'{cls.dependency_name} not exist, please install')
        if cls.dependency_required:
            Color.p('{!} {O}Error: Required app {R}%s{O} was not found' % cls.dependency_name)
            Color.pl('. {W}install @ {C}%s{W}' % cls.dependency_url)
            return True

        else:
            Color.p('{!} {O}Warning: Recommended app {R}%s{O} was not found' % cls.dependency_name)
            Color.pl('. {W}install @ {C}%s{W}' % cls.dependency_url)
            return False

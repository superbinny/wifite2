#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .dependency_win import Dependency
from ..config_win import Configuration


class Hostapd(Dependency):
    dependency_required = False
    dependency_name = 'hostapd'
    dependency_url = 'apt install hostapd'
    pid = None

    @classmethod
    def run(cls, iface, target):

        # with open('/tmp/hostapd.conf', 'w') as fout:
        #    fout.write(f'interface={iface}' + '\n')
        #    fout.write(f'ssid={target.essid}' + '\n')
        #    fout.write(f'channel={target.channel}' + '\n')
        #    fout.write('driver=nl80211\n')
        fout = []
        fout.append(f'interface={iface}')
        fout.append(f'ssid={target.essid}')
        fout.append(f'channel={target.channel}')
        fout.append('driver=nl80211\n')
        Configuration.linux.writefile('/tmp/hostapd.conf', '\n'.join(fout), 'w')
        # command = [
        #     'hostapd',
        #     '/tmp/hostapd.conf'
        # ]
        # process = Process(command)

        return None

    @classmethod
    def stop(cls):
        if hasattr(cls, 'pid') and cls.pid and cls.pid.poll() is None:
            cls.pid.interrupt()
        return None

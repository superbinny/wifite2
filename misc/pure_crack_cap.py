
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# **********************************************************
#       Created:     2026-02-16 7:14:46
#       Filename:    VsErrorParse.py
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
#       Purpose:     基于纯 python写的破解cap文件的工具
#       Copyright:   TJYM(C) 2010 - All Rights Reserved
#       LastModify:  2026-02-16
# **********************************************************

from scapy.all import rdpcap
from scapy.layers.dot11 import Dot11
import hashlib
from BnPlatform.BinnyBase import * 

def print_handshake_packets(handshake_packets):
    for p in handshake_packets:
        print(p)
        
def parse_handshake(pcap_file):
    packets = rdpcap(pcap_file)
    ssid, bssid = None, None
    handshake = []
    for pkt in packets:
        if pkt.haslayer(Dot11):
            if pkt.type == 0 and pkt.subtype == 8:  # Beacon frame
                ssid = pkt.info.decode('utf-8', 'ignore')
                bssid = pkt.addr3
            elif pkt.type == 2 and (pkt.subtype == 5 or pkt.subtype == 4):  # Handshake frames
                handshake.append(pkt)
    return ssid, bssid, handshake

def check_password(ssid, password, bssid, handshake_packets):
    # 简化的密钥派生逻辑（实际需要更复杂的实现）
    pmk = hashlib.pbkdf2_hmac('sha1', password.encode(), ssid.encode(), 4096, 32)
    # 这里需要验证握手包中的 MIC 值
    # 伪代码示例
    print_handshake_packets(handshake_packets)
    print(f'ssid={ssid}, bssid={bssid}, password={password}, pmk={bnStr2Hex(pmk)}')
    return False  # 替换为实际验证逻辑

def crack_handshake(pcap_file, wordlist_path):
    ssid, bssid, handshake = parse_handshake(pcap_file)
    if not ssid or not handshake:
        print("No handshake found in the pcap file.")
        return
    with open(wordlist_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            password = line.strip()
            if check_password(ssid, password, bssid, handshake):
                print(f"Password found: {password}")
                return
    print("Password not found in the wordlist.")

# 示例调用
crack_handshake(r"D:\Crack\海南三优公寓WiFi\hs\handshake__62-17-B6-5E-42-D8_2026-02-15T22-18-03.cap", r"D:\Crack\破解字典\14365003.txt")

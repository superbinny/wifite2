#!/usr/bin/env python

# Note: This script runs Wifite from within a cloned git repo.
# The script `bin/wifite` is designed to be run after installing (from /usr/sbin), not from the cwd.
# 将 wifite 移植到 Windows 下运行
# 原理是利用 zerorpc，进行远程调用：
# 1、linux 下用超级用户运行 server/server_zerorpc.py
#    运行后会显示远程连接的 ip:port
# 2、Windows 下运行 wifite-win --remote-server-port=ip:port
# 3、其他参数可以参考 wifite-win --help
# 调用可以参考以下例子，可以显示 -1 频道：
#     ./wifite-win.py --remote-server-port="192.168.192.130:12999" --show-negative-one
from wifite import __main__win
__main__win.entry_point()

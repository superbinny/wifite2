
#!/usr/bin/env python
# -*- coding: utf-8 -*-
# *********************************************************
#       Created:     2014-11-20   20:02
#       Filename:    server_zerorpc.py
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
#       Purpose:     用于远程在LINUX环境中执行命令，结果通过网络返回
#       Copyright:   TJYM(C) 2014 - All Rights Reserved
#       LastModify:  2014-11-20
# *********************************************************

import zerorpc, gevent
import hashlib
import os, sys

import random
import string

try:
    from util.color_win import Color
except (ValueError, ImportError) as e:
    _para_path = os.path.dirname(os.path.dirname(__file__))
    para_path = os.path.realpath(os.path.join(_para_path, 'wifite'))
    sys.path.append(para_path)
    from util.color_win import Color

# pip install netifaces
import netifaces as ni

try:
    TIME_FACTOR = float(os.environ.get('ZPC_TEST_TIME_FACTOR'))
except TypeError:
    TIME_FACTOR = 0.2

def get_address_from_interface(interface, except_local=True):
    interface_info = ni.ifaddresses(interface)
    if ni.AF_INET in interface_info:
        for link in interface_info[ni.AF_INET]:
            ip_address = link['addr']
            if except_local:
                if ip_address != "127.0.0.1":
                    return ip_address
            else:
                return ip_address
    return None

def get_local_ip_using_netifaces(interface_name=None):
    interfaces = ni.interfaces()
    ip_addresses = []
    if interface_name and interface_name in interfaces:
        ip_address = get_address_from_interface(interface_name)
        if not ip_address is None:
            ip_addresses.append((ip_address, interface_name))
    else:
        for interface in interfaces:
            ip_address = get_address_from_interface(interface)
            if not ip_address is None:
                ip_addresses.append((ip_address, interface))
    return ip_addresses
        
class MyServer(zerorpc.Server):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.init()

    def init(self):
        self.locals = {}
        self.globals = {}

    @staticmethod
    def generate_random_string(length):
        letters = string.ascii_letters + string.digits
        return ''.join(random.choice(letters) for _ in range(length))
    
    def print_error(self, request, ex):
        ex_class_name = str(type(ex))
        ex_class_name = ex_class_name.replace("<class '", '')
        ex_class_name = ex_class_name.replace("'>", '')
        desc = f'Cmd={request}, Class={ex_class_name}, Msg={ex.args[0]}'
        self.debug_error('print_error', desc)
        return desc

    def exec_cmd_ret(self, request):
        result_id = 'result' + MyServer.generate_random_string(6)
        cmd = f"{result_id}={request}"
        self.debug_print("exec_cmd_ret", cmd)
        try:
            exec(cmd, self.globals, self.locals)
        except NameError as ex:
            if "Popen" in cmd:
                cmd = cmd
            desc = self.print_error(request, ex)
            return None, desc
        except Exception as ex:
            desc = self.print_error(request, ex)
            if result_id in self.locals:
                self.locals.pop(result_id)
            return None, desc
        return result_id, self.locals[result_id]
    
    def get_result(self, result):
        if result in self.locals:
            return result, self.locals[result]
        else:
            return result, f'Error:{result} not in locals!'

    def is_debug(self):
        if 'debug' in self.globals:
            return self.globals['debug']
        return False

    def debug_print(self, cmd, msg):
        if self.is_debug():
            Color.pl("{{R}Debug{W}} {C}%s:{W} %s" % (cmd, msg))

    def debug_error(self, cmd, msg):
        Color.pl("{{R}Error{W}} {C}%s:{W} %s" % (cmd, msg))

    def exec_cmd(self, request):
        self.debug_print("exec_cmd", request)
        try:
            exec(request, self.globals, self.locals)
        except Exception as e:
            self.debug_error('exec_cmd', request)
            self.debug_error('e=', '%s' % e)

    def doCommand(self, request, debug=False):
        # print("doCommand in: %s" % request)
        cmd = 'doCommand'
        if request == 'reset_namespace':
            self.init()
        if debug:
            self.globals['debug'] = debug
            cmd += '(Debug mode)'
        self.debug_print(cmd, request)

    def get_file(self, request):
        self.debug_print("get_file", request)
        if os.path.exists(request):
            try:
                f = open(request, 'rb')
                sOut = f.read()
                f.close()
                return sOut
            except:
                return None
        else:
            return None

    def writefile(self, request, data, mode='w'):
        self.debug_print("writefile", "%s, mode=%s" % (request, mode))
        try:
            f = open(request, mode)
            f.write(data)
            f.close()
            return os.path.exists(request)
        except:
            return False
        
    def get_file_md5(self, file_path):
        self.debug_print("get_file_md5", file_path)
        # 获取文件的 md5
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def rename(self, source, destination):
        """
            Renames file 'old' to 'new', works with separate partitions.
            Thanks to hannan.sadar
        """
        self.debug_print("rename", "%s=>%s" % (source, destination))
        if not os.path.exists(source):
            self.debug_error('rename', f"The file {source} not exist!")
            return 'ErrorNotExist'
        else:
            try:
                # 尝试重命名文件
                os.rename(source, destination)
                return 'OK'
            except PermissionError:
                # print("Insufficient permissions")
                return 'ErrorPermissions'
            except FileExistsError:
                # print("The target file already exists")
                return 'ErrorExistDestination'
            except Exception as e:
                # print(f"发生未知错误: {e}")
                return f'ErrorUnknow:{e}'

if __name__ == "__main__":
    Color.pl("{G}Start server ...{W}" )
    server_port = '12999'
    server_ip = '0.0.0.0'
    Color.pl('Listen to {C}%s{W}' % f'{server_ip}:{server_port}')
    ip_addrs = get_local_ip_using_netifaces()
    for ip_addr, interface in ip_addrs:
        ipinfo = f'{ip_addr}:{server_port}'
        Color.pl('Client connect to {C}%s{W} ( Interface={O}%s{W} )' % (ipinfo, interface))
    connet_str = f"tcp://{server_ip}:{server_port}"
    server = MyServer()
    server.bind(connet_str)
    server_task = gevent.spawn(server.run)
    server_task.join()
    print('Done!')

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
import os

import random
import string

# pip install netifaces
import netifaces as ni

def get_local_ip_using_netifaces():
    interfaces = ni.interfaces()
    for interface in interfaces:
        interface_info = ni.ifaddresses(interface)
        if ni.AF_INET in interface_info:
            for link in interface_info[ni.AF_INET]:
                ip_address = link['addr']
                if ip_address != "127.0.0.1":
                    return ip_address
    return None
        
class MyServer():
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
        print('Error: exec_cmd_ret=>%s' % desc)
        return desc

    def exec_cmd_ret(self, request):
        result_id = 'result' + MyServer.generate_random_string(6)
        cmd = f'{result_id}=' + request
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

    def debug_print(self, msg):
        if self.is_debug():
            print(msg)

    def exec_cmd(self, request):
        try:
            self.debug_print(f'exec_cmd {request}')
            exec(request, self.globals, self.locals)
        except Exception as e:
            print('Exec: %s' % request)
            print('Error: %s' % e)

    def doCommand(self, request):
        if request == 'reset_namespace':
            self.init()
        return f"doCommand, {request}"

    def get_file(self, request):
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

    def set_file(self, request, data, overwrite=False):
        if os.path.exists(request):
            if overwrite:
                os.remove(request)
            else:
                return True
        try:
            f = open(request, 'wb')
            f.write(data)
            f.close()
            return os.path.exists(f)
        except:
            return False
        
    def get_file_md5(self, file_path):
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
        if not os.path.exists(source):
            print(f"The file {source} not exist!")
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
    print('Start server ...')
    server_port = '12999'
    server_ip = '0.0.0.0'
    print(f'Listen to {server_ip}:{server_port}')
    print(f'Client connect to {get_local_ip_using_netifaces()}:{server_port}')
    connet_str = f"tcp://{server_ip}:{server_port}"
    server = zerorpc.Server(MyServer())
    server.bind(connet_str)
    server_task = gevent.spawn(server.run)
    server_task.join()
    print('Done!')
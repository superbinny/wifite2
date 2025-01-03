#!/usr/bin/env python
# -*- coding: utf-8 -*-
# *********************************************************
#       Created:     2014-11-17   10:00
#       Filename:    remote_linux_system.py
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
#       LastModify:  2014-11-17
# *********************************************************

import errno  # Error numbers
import hashlib
import os
import random  # Generating a random MAC address.
import time

# pip install pickle
import pickle

# pip install zerorpc
import zerorpc

class FileType():
    is_remote = False
    filename = ''

# test_zerorpc(server_ip='192.168.192.130', server_port='12999', isEmul=False)
    
# 用于序列化所有的对象
class SerialObject():
    def __init__(self, emul_path):
        self.emul_path = emul_path

    def get_emul_file(self, cmd):
        command = '%s' % cmd
        md5 = hashlib.md5(command)
        return os.path.join(self.emul_path, md5.hexdigest() + '.pickle')

    def save(self, cmd, data):
        fname = self.get_emul_file(cmd)
        with open(fname, 'wb') as f:
            pickle.dump(data, f)

    def load(self, cmd):
        result = None
        fname = self.get_emul_file(cmd)
        if os.path.exists(fname):
            with open(fname, 'rb') as f:
                result = pickle.load(f)
        return result


class TimeoutError(Exception):
    pass

class remote_linux_system():
    
    def __init__(self,
                 server_ip,
                 server_port,
                 isEmul=False,
                 isSave=False,
                 emul_path='Emul',
                 timeout=500):
        
        self.setEmulPath(emul_path)
        self.Emul = isEmul
        self.server_ip = server_ip
        self.server_port = server_port
        self.locals = {}
        self.globals = {}
        self.IsSave = isSave
    
    def get_connect(self):
        self.connect_str = f"tcp://{self.server_ip}:{self.server_port}"
        if not self.Emul:
            try:
                # client = zerorpc.Client()
                # client.set_heartbeat(1, 3)  # 心跳间隔1秒，超时时间3秒
                # print(f'Connect to {self.connect_str} ...')
                client = zerorpc.Client()
                client.connect(self.connect_str)
            except Exception as e:
                print('Error: get_connect %s' % e)
        # reset_namespace = client.doCommand('reset_namespace')
        # print(reset_namespace)
        return client
    
    def reset(self):
        self.ResetNamespace()
        
    def setEmulPath(self, p):
        self.emul_path = p
        self.serial = SerialObject(self.emul_path)

    def Exec_timeout(self, cmd, _hash=None, timeout=60):
        """带超时的命令执行"""
        if _hash is None:
            _hash = cmd
        if self.Emul:
            result = self.serial.load(_hash)
        else:
            # print('exec_cmd_ret:\t%s' % cmd)
            result = self.client.exec_cmd_ret(cmd, async_=True)

        t_beginning = time.time()
        seconds_passed = 0
        while not self.Emul:
            if self.poll('result') is not None:
                break
            seconds_passed = time.time() - t_beginning
            if timeout and seconds_passed > timeout:
                self.os_kill('result')
                raise TimeoutError(cmd, timeout)
            time.sleep(0.1)
        if self.IsSave and not self.Emul:
            self.serial.save(_hash, result)
        return result

    def exec_cmd_ret(self, cmd, _hash=None):
        if _hash is None:
            _hash = cmd
        result = None
        if self.Emul:
            result = self.serial.load(_hash)
        else:
            # print 'exec_cmd_ret:\t', cmd
            try:
                result = self.client.exec_cmd_ret(cmd, async_=True)
            except zerorpc.RemoteError:
                print('Error: exec_cmd_ret zerorpc.RemoteError')
            except zerorpc.TimeoutExpired:
                print('Error: exec_cmd_ret zerorpc.TimeoutExpired')
            except Exception as ex:
                print('Error: exec_cmd_ret %s' % ex.args[0])

        if self.IsSave and not self.Emul:
            self.serial.save(_hash, result)
        # Wait for the result.   If the server encountered an error,
        # an speedy.RemoteException will be thrown.
        return result
    
    def get_result(self, result):
        return self.client.result(result, async_=True)
    
    def Do(self, f, _hash=None):
        if _hash is None:
            _hash = f
        result = None
        if self.Emul:
            result = self.serial.load(_hash)
        else:
            # print 'exec_cmd:\t', f
            try:
                result = self.client.exec_cmd(f, async_=True)
            except Exception as e:
                print('Error: Do %s' % e)

        if self.IsSave and not self.Emul:
            self.serial.save(_hash, result)

        return result == f

    def ResetNamespace(self):
        # print 'doCommand:\t', f
        '''
from subprocess import Popen, call, PIPE
import os, platform
import shutil
from signal import SIGINT, SIGTERM
DN = open(os.devnull, 'w')
        '''
        if not self.Emul:
            self.client.doCommand('reset_namespace', async_=True)
        self.Do('from subprocess import Popen, call, PIPE')
        self.Do('import os, platform')
        self.Do('import shutil')  # copy
        self.Do('from signal import SIGINT, SIGTERM')
        self.Do("DN=open(os.devnull, 'w')")
        self.isLinux = self.exec_cmd_ret('platform.system()') == 'Linux'
        self.os_sep = self.exec_cmd_ret('os.sep')
        self.os_name = self.exec_cmd_ret('os.name')

    # 有关于os的几个操作
    def os_getuid(self):
        return self.exec_cmd_ret('os.getuid()')

    def os_uname(self):
        return self.exec_cmd_ret('os.uname()')

    def os_listdir(self, p):
        return self.exec_cmd_ret("os.listdir('%s')" % p)

    def exists(self, p):
        if type(p) is FileType:
            if p.is_remote:
                filename = p.filename
            else:
                return os.path.exists(p.filename)
        else:
            filename = p
        cmd = f"os.path.exists('{filename}')"
        # print(cmd)
        reslt = self.exec_cmd_ret(cmd)
        if reslt is None:
            reslt = False
        # print(cmd, '=', reslt)
        return reslt

    def os_kill(self, process, sign='signal.SIGTERM'):
        if self.isLinux:
            # pgid = self.exec_cmd_ret("os.getpgid(%s.pid)" % process)
            self.Do("os.kill(%s.pid, %s)" % (process, sign))
            self.Do("os.waitpid(%s.pid, 0)" % process)
        else:
            self.Do("%s.terminate()" % process)

    def os_kill_pid(self, pid):
        # pgid = self.exec_cmd_ret("os.getpgid(%s.pid)" % process)
        self.Do("os.kill(%d, %s)" % (pid, 'SIGTERM'))
        self.Do("os.waitpid(%d, 0)" % pid)

    def remove_file(self, filename):
        """
            Attempts to remove a file. Does not throw error if file is not found.
        """
        self.Do("os.remove('%s')" % filename)

    def remove_dirs(self, filename):
        self.Do('import shutil')
        self.Do("shutil.rmtree('%s')" % filename)

    def findfiles(self, dirname, pattern):
        cwd = self.getcwd()  # 保存当前工作目录
        if dirname:
            self.chdir(dirname)

        result = []
        files = self.list_by_pattern(pattern)
        # 恢复工作目录
        self.chdir(cwd)
        return files

    def list_by_pattern(self, pattern):
        self.Do('import glob')
        # command = "'%%s' %% [k for k in glob.iglob('%s')]" % pattern
        # 此处可以用glob.glob(pattern) 返回所有结果
        command = "[k for k in glob.iglob('%s')]" % pattern
        return self.exec_cmd_ret(command)

    # 删除所有与filename匹配的文件和目录
    def remove_files(self, dirname, pattern):
        files = self.findfiles(dirname, pattern)
        for f in files:
            fullname = self.join(dirname, f)
            if self.exists(fullname):
                if self.isdir(fullname):
                    self.remove_dirs(fullname)
                else:
                    self.remove_file(fullname)

    # os功能
    def getcwd(self):
        return self.exec_cmd_ret("os.getcwd()")
    
    def isfile(self, f):
        return self.exec_cmd_ret(f"os.path.isfile('{f}')")
    
    def seek(self, f, num):
        return self.Do(f"{f}.seek({num})")
    
    def truncate(self, f):
        return self.Do(f"{f}.truncate()")

    def isdir(self, f):
        return self.exec_cmd_ret(f"os.path.isdir('{f}')")

    def join(self, dirname, subname):
        return self.exec_cmd_ret("os.path.join('%s', '%s')" % (dirname, subname))

    def chdir(self, filename):
        self.Do("os.chdir('%s')" % filename)

    def dirname(self, filename):
        return self.exec_cmd_ret("os.path.dirname('%s')" % filename)

    def makedirs(self, directory):
        # 一次性建立多层目录
        self.Do("os.makedirs('%s')" % directory)

    def mkdir(self, directory):
        # 建立单层目录
        self.Do("os.mkdir('%s')" % directory)

    def rmdir(self, filename):
        self.Do("os.rmdir('%s')" % filename)

    def unlink(self, filename):
        self.Do("os.unlink('%s')" % filename)

    def basename(self, fname):
        return self.exec_cmd_ret("os.path.basename('%s')" % fname)

    def copy(self, src, dst):
        self.Do("shutil.copy('%s', '%s')" % (src, dst))

    def copy_from_remote(self, src, dst):
        '''
        将远程文件拷贝到本地
        '''
        try:
            result = self.client.get_file(src, async_=True)
            if result is not None:
                par_path = os.path.dirname(dst)
                if not os.path.exists(par_path):
                    os.makedirs(par_path)
                f = open(dst, 'wb')
                f.write(result)
                f.close()
        except Exception as e:
            print('Error: copy_from_remote %s' % e.message)

    def copy_to_remote(self, src, dst, overwrite=True):
        '''
        将本地文件拷贝到远程
        '''
        if not overwrite and self.exist(dst):
            return True
        try:
            f = open(src, 'rb')
            data = f.read()
            f.close()
            result = self.client.set_file(dst, data, overwrite=True, async_=True)
            return self.exist(dst)
        except Exception as e:
            print('Error: copy_to_remote %s' % e.message)

    def rename(self, old, new):
        result = self.client.rename(old, new, async_=True)
        return result

    # 以下几个函数是关于文件读写和关闭的
    # 使用 fhandle 是担心重名
    def open(self, filename, mode, fhandle='fhandle', encoding='utf-8'):
        if encoding is None:
            cmd = f"{fhandle}=open('{filename}', '{mode}')"
        else:
            cmd = f"{fhandle}=open('{filename}', '{mode}', encoding='{encoding}')"
        self.Do(cmd)

    def read(self, fhandle):
        return self.exec_cmd_ret(f"{fhandle}.read()")

    def readfile(self, p, mode='r', encoding='utf-8', fhandle='fhandle'):
        if type(p) is FileType:
            filename = p.filename
            if not p.is_remote:
                with open(filename, mode, encoding=encoding) as f:
                    lines = f.read()
                    f.close()
                return lines
        else:
            filename = p

        self.open(filename, mode=mode, fhandle=fhandle, encoding=encoding)
        lines = self.read(fhandle=fhandle)
        self.close(fhandle=fhandle)
        return lines

    def clearfile(self, filename, fhandle='fhandle'):
        self.open(filename, 'w', fhandle=fhandle)
        self.close(fhandle=fhandle)

    # 获取当前运行的服务器的PID
    def get_server_pid(self):
        return self.exec_cmd_ret("os.getpid()")

    def do_split(self, line, symbol, max_col=0):
        lines = []
        pstart = 0
        pend = 0
        if max_col == 0:  # 标题列
            line = line.strip()
            tmp_lines = line.split(symbol)
            for l in tmp_lines:
                if l != '':
                    lines.append(l)
            return lines
        bSpace = False
        index = 0
        for i in range(len(line)):
            if line[i] == symbol and not bSpace:
                index += 1
                if index == max_col:
                    lines.append(line[pstart:].strip())
                    return lines
                else:
                    lines.append(line[pstart:i])
                bSpace = True
            elif bSpace and line[i] != symbol:
                pstart = i
                bSpace = False
        lines.append(line[pstart:].strip())
        return lines

    # 获取当前服务器产生的所有进程
    def get_table_items(self, lst, symbol, titles=[]):
        index = 0
        values = []
        for line in lst.split('\n'):
            if len(line) == 0: continue
            if len(titles) == 0 and index == 0:
                titles = self.do_split(line, symbol)
            else:
                values.append(self.do_split(line, symbol, len(titles)))
            index += 1
        return titles, values

    def get_server_sub_pids(self):
        pslist = self.program_communicate(['ps', '-ef'])
        '''
        UID      PID     PPID C STIME TTY      TIME     CMD
        root     16812     2  0 11:38 ?        00:00:00 [kworker/0:0]
        root     16828     2  0 11:43 ?        00:00:00 [kworker/u2:3]
        root     16829     2  0 11:43 ?        00:00:00 [kworker/0:2]
        root     16830 14889  0 11:43 pts/0    00:00:00 ps -ef        
        '''
        pids = {}
        titles, values = self.get_table_items(pslist[0].decode(), ' ')
        pid = self.get_server_pid()
        # 得到所有的ppid和该pid相同的项目
        index_PPID = titles.index('PPID')
        index_PID = titles.index('PID')
        index_CMD = titles.index('CMD')
        for line in values:
            if int(line[index_PPID]) == pid:
                pids[int(line[index_PID])] = line[index_CMD]
        return pids

    # 删除服务端产生的所有子进程
    def kill_all_subprocess(self):
        pids = self.get_server_sub_pids()
        for p in pids.keys():
            self.os_kill_pid(p)

    def send_interrupt(self, process):
        """
            Sends interrupt signal to process's PID.
        """
        try:
            self.os_kill(process, 'SIGINT')
        except OSError:
            pass  # process cannot be killed
        except TypeError:
            pass  # pid is incorrect type
        except UnboundLocalError:
            pass  # 'process' is not defined
        except AttributeError:
            pass  # Trying to kill "None"
        except:
            pass

    def close(self, fhandle):
        self.Do("%s.close()" % fhandle)

    def wait(self, handle):
        self.Do('%s.wait()' % handle)

    # ----------------------------------------------------------------------
    # 相当于：
    # proc = Popen(program, stdout=PIPE, stderr=PIPE)
    # proc.communicate()
    def program_communicate(self, program, stdout='PIPE', stderr='PIPE'):
        result = None
        command = "Popen(%s, stdout=%s, stderr=%s).communicate()" % (program, stdout, stderr)
        result = self.exec_cmd_ret(command)
        return result

    # 相当于：
    # proc = Popen(program, stdout=PIPE, stderr=PIPE)
    # proc.wait()
    # proc.communicate()
    def program_communicate_wait(self, program, stdout='PIPE', stderr='PIPE', shell='False', timeout=None):
        result = None
        cmd = "proctemp=Popen(%s, stdout=%s, stderr=%s, shell=%s)" % (program, stdout, stderr, shell)
        DEFAULT_TIMEOUT = 5
        #if timeout is not None:
        #    BnSpeedy.set_default_timeout(timeout)
        self.Do(cmd)
        self.wait('proctemp')
        result = self.exec_cmd_ret("proctemp.communicate()", cmd + "proctemp.communicate()")
        # BnSpeedy.set_default_timeout(DEFAULT_TIMEOUT)
        return result

    def program_exists(self, program):
        """
            Uses 'which' (linux command) to check if a program is installed.
        """
        txt = self.program_communicate("['which', '%s']" % program, stdout='PIPE', stderr='PIPE')
        if txt[0].strip() == '' and txt[1].strip() == '':
            return False
        if txt[0].strip() != '' and txt[1].strip() == '':
            return True

        return not (txt[1].strip() == '' or (txt[1].decode()).find('no %s in' % program) != -1)

    def call_program(self, program, stdout='DN', stderr='DN'):
        self.Do("call(%s, stdout=%s, stderr=%s)" % (program, stdout, stderr))
    
    def DoPopen(self, command, result_id='', stdout='DN', stderr='DN'):
        if result_id != '':
            command = "%s=Popen(%s, stdout=%s, stderr=%s)" % (result_id, command, stdout, stderr)
        else:
            command = "Popen(%s, stdout=%s, stderr=%s)" % (command, stdout, stderr)
        self.Do(command)
    
    @staticmethod
    def fix_command(command):
        paras = command.split(',')
        cmd = []
        for para in paras:
            if len(para.strip()) != 0:
                cmd.append(para.strip())
        return ','.join(cmd)

    # 实现一个完整的 Popen
    def Popen(self, args, bufsize=-1, executable=None,
                 stdin=None, stdout=None, stderr=None,
                 preexec_fn=None, close_fds=True,
                 shell=False, cwd=None, env=None, universal_newlines=None,
                 startupinfo=None, creationflags=0,
                 restore_signals=True, start_new_session=False,
                 pass_fds=(), *, user=None, group=None, extra_groups=None,
                 encoding=None, errors=None, text=None, umask=-1, pipesize=-1,
                 process_group=None, result_id=None):

        if result_id is None:
            result_id = 'resultTemp'

        command = f'''{result_id}=Popen(args={args}, bufsize={bufsize}, executable={executable}, stdin={stdin}, stdout={stdout}, stderr={stderr},
                            preexec_fn={preexec_fn}, close_fds={close_fds},
                            shell={shell}, cwd={cwd}, env={env}, universal_newlines={universal_newlines},
                            startupinfo={startupinfo}, creationflags={creationflags},
                            restore_signals={restore_signals}, start_new_session={start_new_session},
                            pass_fds={pass_fds}, user={user}, group={group}, extra_groups={extra_groups},
                            encoding={encoding}, errors={errors}, text={text}, umask={umask}, pipesize={pipesize},
                            process_group={process_group})
                    '''
        command = remote_linux_system.fix_command(command)
        # print(command)
        self.Do(command)
        pid = self.exec_cmd_ret(f'{result_id}.pid')
        if stdout == 'PIPE' or stderr == 'PIPE':
            command = f'{result_id}.communicate()'
            output = self.exec_cmd_ret(command)
        else:
            output = None
        return result_id, pid, output
    
    def stdout_readline(self, result_id):
        return self.exec_cmd_ret('%s.stdout.readline()' % result_id)

    def stdout_read(self, result_id):
        return self.exec_cmd_ret('%s.stdout.read()' % result_id)

    def poll(self, result_id):
        return self.exec_cmd_ret('%s.poll()' % result_id)

    def poll_interrupt(self, result_id):
        return self.exec_cmd_ret('%s.interrupt()' % result_id)

    def communicate(self, result_id):
        return self.exec_cmd_ret('%s.communicate()' % result_id)

    def mkdtemp(self, prefix):
        self.Do('from tempfile import mkdtemp')
        return self.exec_cmd_ret("mkdtemp(prefix='%s')" % prefix)

    # 有关网络的操作
    # 获取某一个接口的MAC地址
    def get_mac_address(self, iface):
        """
            Returns MAC address of "iface".
        """
        '''
        mon0      Link encap:UNSPEC  HWaddr C8-3A-35-CC-D5-87-00-00-00-00-00-00-00-00-00-00  
              UP BROADCAST NOTRAILERS RUNNING PROMISC ALLMULTI  MTU:1500  Metric:1
              RX packets:60042 errors:0 dropped:21924 overruns:0 frame:0
              TX packets:0 errors:0 dropped:0 overruns:0 carrier:0
              collisions:0 txqueuelen:1000 
              RX bytes:4976733 (4.7 MiB)  TX bytes:0 (0.0 B)
              
        wlan0mon: flags=4098<BROADCAST,MULTICAST>  mtu 1500
            unspec E8-39-DF-96-4E-BF-00-00-00-00-00-00-00-00-00-00  txqueuelen 1000  (UNSPEC)
            RX packets 7355  bytes 1552008 (1.4 MiB)
            RX errors 0  dropped 7355  overruns 0  frame 0
            TX packets 0  bytes 0 (0.0 B)
            TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0
            
        eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
            inet 192.168.99.107  netmask 255.255.255.0  broadcast 192.168.99.255
            inet6 fe80::c7c9:710b:25ae:b5b5  prefixlen 64  scopeid 0x20<link>
            ether 00:24:54:bd:46:dc  txqueuelen 1000  (Ethernet)
            RX packets 554  bytes 52256 (51.0 KiB)
            RX errors 0  dropped 0  overruns 0  frame 0
            TX packets 402  bytes 93665 (91.4 KiB)
            TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0
            device interrupt 19
        '''
        ifconfig_communicate = self.program_communicate_wait(['ifconfig', iface])
        mac = ''
        multi_lines = ifconfig_communicate[0].split('\n')
        flags = ['HWaddr ', 'ether ', 'unspec ']
        for line in multi_lines:
            for flag in flags:
                if line.find(flag) != -1:
                    left_str = line[line.find(flag):]
                    mac = left_str.split(' ')[1]
                    break
            if mac != '': break

        if mac.find('-') != -1: mac = mac.replace('-', ':')
        if len(mac) > 17: mac = mac[0:17]
        return mac

    # 获取所有处于监控状态的的接口
    def get_all_monitors(self):
        iwconfig_communicate = self.program_communicate(['iwconfig'], stdout='PIPE', stderr='DN')
        iface = ''
        monitors = []
        for line in (iwconfig_communicate[0]).decode().split('\n'):
            if len(line) == 0: continue
            if ord(line[0]) != 32:  # Doesn't start with space
                iface = line[:line.find(' ')]  # is the interface
            if line.find('Mode:Monitor') != -1:
                monitors.append(iface)
        return monitors

    def get_all_interface(self):
        interfaces = []
        airmon_ng_communicate = linux.program_communicate(['airmon-ng'], stdout='PIPE', stderr='DN')
        for line in airmon_ng_communicate[0].split('\n'):
            if len(line) == 0 or line.startswith('Interface'): continue
            # interfaces.append(line[:line.find('\t')])
            interfaces.append(line)
        return interfaces

    def get_monitor_from_interfaces(self, interfaces):
        if len(interfaces) != 0:
            # 'wlan2\t\tRalink RT2870/3070\trt2800usb - [phy0]'
            if interfaces[0].startswith('wlan'):
                return interfaces[0][:interfaces[0].find('\t')]

            titles, values = self.get_table_items('\n'.join(interfaces), '\t')
            print(interfaces)
            if 'Interface' in titles:
                index = titles.index('Interface')
                #print('Index=%d, %s' % (index, interfaces))
                if len(values) > 0:
                    return values[0][index]
        return ''

    def generate_random_mac(self, old_mac):
        """
            Generates a random MAC address.
            Keeps the same vender (first 6 chars) of the old MAC address (old_mac).
            Returns string in format old_mac[0:9] + :XX:XX:XX where X is random hex
        """
        random.seed()
        new_mac = old_mac[:8].lower().replace('-', ':')
        for i in range(0, 6):
            if i % 2 == 0: new_mac += ':'
            new_mac += '0123456789abcdef'[random.randint(0, 15)]

        # Prevent generating the same MAC address via recursion.
        if new_mac == old_mac:
            new_mac = self.generate_random_mac(old_mac)
        return new_mac

    def enable_monitor_mode(self, iface):
        """
            Uses airmon-ng to put a device into Monitor Mode.
            Then uses the get_iface() method to retrieve the new interface's name.
            Sets global variable g.IFACE_TO_TAKE_DOWN as well.
            Returns the name of the interface in monitor mode.
        """
        self.call_program(['airmon-ng', 'start', iface], stdout='DN', stderr='DN')

    def disable_monitor_mode(self, iface):
        """
            The program may have enabled monitor mode on a wireless interface.
            We want to disable this before we exit, so we will do that.
        """
        linux.call_program(['airmon-ng', 'stop', iface], stdout='DN', stderr='DN')

    @staticmethod
    def bnStr2Hex(sInput):
        sOut = ''
        # print('bnStr2Hex=', sInput, type(sInput))
        for i in sInput:
            if type(i) is int:
                sOut += '%02x' % i
            else:
                sOut += '%02x' % (ord(i))
        # print('bnStr2Hex out=', sOut, type(sOut))
        return sOut

    @staticmethod
    def bnSaveToHex(file_name, data, encoding=None):
        try:
            f = open(file_name, 'wb')
            data = remote_linux_system.bnStr2Hex(data)
            bin_data = bytes(data, encoding=encoding)
            # print('data=', data, type(data))
            f.write(bin_data)
            f.close()
        except Exception as e:
            print('bnSaveToHex error', e)

    @staticmethod
    def bnSetFileData(file_name, data, encoding='utf-8'):
        """
        put the data to special file
        """
        try:
            if encoding is None:
                if isinstance(data, str):
                    f = open(file_name, 'w')
                else:
                    f = open(file_name, 'wb')
                f.write(data)
            else:
                import codecs
                f = codecs.open(file_name, 'w', encoding)
                f.write(data)
            f.close()

        except Exception as e:
            print('bnSetFileData encode %s error' % encoding, e)
            remote_linux_system.bnSaveToHex(file_name + '.error', data, encoding)
            return False
        return True

if __name__ == '__main__':
    server_ip = '127.0.0.1'
    server_port = 12999
    
    linux = remote_linux_system(server_ip=server_ip, server_port=server_port)
    linux.connect()
    print(linux.exec_cmd_ret('os.name') + linux.get_server_pid())

    fsrc = '/etc/passwd'
    fdst = 'd:\\passwd'
    if os.path.exists(fdst):
        os.remove(fdst)
    if linux.exists(fsrc):
        basename = linux.basename(fsrc)
        linux.copy_from_remote(fsrc, fdst)
        if os.path.exists(fdst):
            os.remove(fdst)
            print('Ok copy_from_remote')
        else:
            print('Error copy_from_remote')

    pslist = linux.get_server_sub_pids()

    # 测试程序运行
    # 获取所有处于监视状态的接口
    monitors = linux.get_all_monitors()
    if len(monitors) == 0:
        interfaces = linux.get_all_interface()

        if len(interfaces) != 0:
            monitor = linux.get_monitor_from_interfaces(interfaces)
            linux.enable_monitor_mode(monitor)
            monitors = linux.get_all_monitors()

    if len(monitors):
        linux_temp = linux.mkdtemp(prefix='wifite')
        if not linux_temp.endswith(linux.os_sep):
            linux_temp += linux.os_sep

        command = ['airodump-ng',
                   '-a',  # only show associated clients
                   '-w', linux_temp + 'wifite']  # output file
        channel = 0
        if channel != 0:
            command.append('-c')
            command.append(str(channel))
        command.append(monitors[0])

        proc_airodump_ng = 'proc_airodump_ng'

        linux.DoPopen(command, proc_airodump_ng, stdout='DN', stderr='DN')
        time.sleep(30)
        print('before interrupt:\n' + linux.get_server_sub_pids())
        linux.send_interrupt(proc_airodump_ng)
        print('after interrupt:\n' + linux.get_server_sub_pids())
        if linux.exists(linux_temp + 'wifite-01.csv'):
            s = linux.readfile(linux_temp + 'wifite-01.csv')
            remote_linux_system.bnSetFileData('e:/abc.csv', s)
            print(s)

        linux.disable_monitor_mode(monitors[0])

    linux.kill_all_subprocess()
    linux.remove_files('/tmp', 'wifite*')

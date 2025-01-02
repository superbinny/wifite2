import zerorpc
import socket
import os
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

    def exec_cmd_ret(self, request):
        cmd = 'result=' + request
        exec(cmd, self.globals, self.locals)
        #print(self.locals)
        return self.locals['result']

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


if __name__ == "__main__":
    print('Start server ...')
    server_port = '12999'
    server_ip = '0.0.0.0'
    print(f'Listen to {server_ip}:{server_port}')
    print(f'Client connect to {get_local_ip_using_netifaces()}:{server_port}')
    connet_str = f"tcp://{server_ip}:{server_port}"
    server = zerorpc.Server(MyServer())
    server.bind(connet_str)
    server.run()
    print('Done!')
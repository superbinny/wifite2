#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import contextlib
import time
# import signal
# import os
# from subprocess import Popen, PIPE
from ..util.color_win import Color
from ..config_win import Configuration, LinuxPopen, generate_random_string


class Process(object):
    """ Represents a running/ran process """

    @staticmethod
    def devnull():
        """ Helper method for opening devnull """
        # fhandle = 'fhandle'
        # Configuration.linux.open('/dev/null', fhandle=fhandle, mode='w')
        # return fhandle
        # 因为 DN 在初始化的时候已经计算
        return 'DN'

    @staticmethod
    def split_command(command):
        command_list = command.split(' ')
        commands = []
        for cmd in command_list:
            if cmd.strip() != '':
                commands.append(f"'{cmd}'")
        result = ','.join(commands)
        return '[%s]' % result
    
    @staticmethod
    def call(command, cwd=None, shell=False):
        """
            Calls a command (either string or list of args).
            Returns tuple:
                (stdout, stderr)
        """
        if type(command) is not str or ' ' in command or shell:
            shell = True
            if Configuration.verbose > 1:
                Color.pe('\n {C}[?] {W} Executing (Shell): {B}%s{W}' % command)
            command = Process.split_command(command)
        else:
            shell = False
            if Configuration.verbose > 1:
                Color.pe('\n {C}[?]{W} Executing: {B}%s{W}' % command)

        # pid = Popen(command, cwd=cwd, stdout=PIPE, stderr=PIPE, shell=shell)
        # pid.wait()
        # (stdout, stderr) = pid.communicate()
        pid = Configuration.linux.program_communicate(command)
        stdout = pid[0]
        stderr = pid[1]

        # Python 3 compatibility
        if type(stdout) is bytes:
            stdout = stdout.decode('utf-8')
        if type(stderr) is bytes:
            stderr = stderr.decode('utf-8')

        if Configuration.verbose > 1 and stdout is not None and stdout.strip() != '':
            Color.pe('{P} [stdout] %s{W}' % '\n [stdout] '.join(stdout.strip().split('\n')))
        if Configuration.verbose > 1 and stderr is not None and stderr.strip() != '':
            Color.pe('{P} [stderr] %s{W}' % '\n [stderr] '.join(stderr.strip().split('\n')))

        return stdout, stderr

    @staticmethod
    def exists(program):
        """ Checks if program is installed on this system """

        if Configuration.initialized and program in set(Configuration.existing_commands.keys()):
            return Configuration.existing_commands[program]

        exist = Configuration.linux.program_exists(program)
        # p2 = Process(['which', program])
        # stdout = p2.stdout().strip()
        # stderr = p2.stderr().strip()

        # exist = not stdout == stderr == ''
        if Configuration.initialized:
            Configuration.existing_commands.update({program: exist})
        return exist

    @staticmethod
    def get_result_id(command):
        return command[0].replace('-', '_')
        
    def __init__(self, command, devnull=False, stdout='PIPE', stderr='PIPE', cwd='None', bufsize='0', stdin='PIPE', result_id=None):
        """ Starts executing command """

        if type(command) is str:
            # Commands have to be a list
            command = command.split(' ')

        self.command = command

        if Configuration.verbose > 1:
            Color.pe('\n {C}[?] {W} Executing: {B}%s{W}' % ' '.join(command))

        self.out = None
        self.err = None
        if devnull:
            sout = Process.devnull()
            serr = Process.devnull()
        else:
            sout = stdout
            serr = stderr

        self.start_time = time.time()
        # self.pid = Popen(command, stdout=sout, stderr=serr, stdin=stdin, cwd=cwd, bufsize=bufsize)
        if result_id is None:
            self.result_id = Process.get_result_id(command) + generate_random_string(6)
        else:
            self.result_id = result_id

        self.popen = LinuxPopen(Configuration.linux, command, stdout=sout, stderr=serr, stdin=stdin, cwd=cwd, bufsize=bufsize, result_id=self.result_id)
        self.result_id = self.popen.result_id
        self.pid = self.popen.pid
        time.sleep(0.1)

     # def __del__(self):
     #     """
     #        Ran when object is GC'd.
     #        If process is still running at this point, it should die.
     #     """
     #     with contextlib.suppress(AttributeError):
     #         if self.pid and self.popen.poll(self.result_id) is None:
     #             self.interrupt(self.result_id)

    def stdout(self):
        """ Waits for process to finish, returns stdout output """
        self.get_output()
        if Configuration.verbose > 1 and self.out is not None and self.out.strip() != '':
            Color.pe('{P} [stdout] %s{W}' % '\n [stdout] '.join(self.out.strip().split('\n')))
        return self.out

    def stderr(self):
        """ Waits for process to finish, returns stderr output """
        self.get_output()
        if Configuration.verbose > 1 and self.err is not None and self.err.strip() != '':
            Color.pe('{P} [stderr] %s{W}' % '\n [stderr] '.join(self.err.strip().split('\n')))
        return self.err

    def stdoutln(self):
        # return self.pid.stdout.readline()
        return Configuration.linux.stdout_readline(self.result_id)

    def stderrln(self):
        # return self.pid.stderr.readline()
        return Configuration.linux.stderr_readline(self.result_id)

    def stdin(self, text):
        # if self.pid.stdin:
        #     self.pid.stdin.write(text.encode('utf-8'))
        #     self.pid.stdin.flush()
        if self.popen.stdin == 'PIPE':
            Configuration.linux.stdin_write(self.result_id, text.encode('utf-8'))
            Configuration.linux.stdin_flush(self.result_id)

    def get_output(self):
        """ Waits for process to finish, sets stdout & stderr """
        #if self.pid.poll() is None:
        #    self.pid.wait()
        #if self.out is None:
        #    (self.out, self.err) = self.pid.communicate()
        self.out = self.popen.output[0]
        if type(self.out) is bytes:
            self.out = self.out.decode('utf-8')

        self.err = self.popen.output[1]
        if type(self.err) is bytes:
            self.err = self.err.decode('utf-8')

        return self.out, self.err

    def poll(self):
        """ Returns exit code if process is dead, otherwise 'None' """
        # return self.pid.poll()
        return Configuration.linux.poll(self.result_id)

    def wait(self):
        # self.pid.wait()
        Configuration.linux.wait(self.result_id)
        
    def kill(self):
        pid = self.pid
        if pid is None:
            pid = 0

        cmd = self.command
        if type(cmd) is list:
            cmd = ' '.join(cmd)

        if Configuration.verbose > 1:
            if pid:
                Color.pe('\n {C}[?] {W} sending interrupt to PID %d (%s)' % (pid, cmd))
            else:
                Color.pe('\n {C}[?] {W} sending interrupt to Process %s (%s)' % (result_id, cmd))

        if pid:
            Configuration.linux.kill_pid(pid, 'SIGINT')
        else:
            Configuration.linux.kill(result_id, 'SIGINT')

    def running_time(self):
        """ Returns number of seconds since process was started """
        return int(time.time() - self.start_time)

    def interrupt(self, wait_time=2.0):
        """
            Send interrupt to current process.
            If process fails to exit within `wait_time` seconds, terminates it.
        """
        try:
            self._extracted_from_interrupt_7(wait_time)
        except OSError as e:
            if 'No such process' in e.__str__():
                return
            raise e  # process cannot be killed

    # TODO Rename this here and in `interrupt`
    def _extracted_from_interrupt_7(self, wait_time):
                
        self.kill()

        start_time = time.time()  # Time since Interrupt was sent
        while self.poll() is None:
            # Process is still running
            try:
                time.sleep(0.1)
                if time.time() - start_time > wait_time:
                    # We waited too long for process to die, terminate it.
                    if Configuration.verbose > 1:
                        Color.pe('\n {C}[?] {W} Waited > %0.2f seconds for process to die, killing it' % wait_time)
                    self.kill()
                    # self.pid.terminate()
                    break
            except KeyboardInterrupt:
                # wait the cleanup
                continue


if __name__ == '__main__':
    from ..config_win import init_linux
    server_ip = '192.168.192.130'
    server_port = '12999'
    linux = init_linux(server_ip=server_ip, server_port=server_port)
    Configuration.initialize(linux=linux, load_interface=False)
    command = ['ls']
    # p = Process(command)
    result_id = Process.get_result_id(command) + generate_random_string(6)
    p = LinuxPopen(Configuration.linux, command, result_id=result_id)
    print((p.stdout()))
    print((p.stderr()))
    p.interrupt(result_id)

    # Calling as list of arguments
    command = ['ls', '-lah']
    (out, err) = Process.call(command)
    print(out)
    print(err)

    print('\n---------------------\n')

    # Calling as string
    command = 'ls -l | head -2'
    (out, err) = Process.call(command)
    print(out)
    print(err)

    print(f""""reaver" exists: {Process.exists('reaver')}""")

    # Test on never-ending process
    p = Process('yes')
    print('Running yes...')
    time.sleep(1)
    print('yes should stop now')
    # After program loses reference to instance in 'p', process dies.

#!/usr/bin/env python
# -*- coding: utf-8 -*-

from time import sleep, time
import sys

from ..config_win import Configuration
from ..tools.airodump_win import Airodump
from ..util.color_win import Color
from shlex import quote as shlex_quote

# 原来程序中，通过 Ctrl+C 来终止程序，这容易造成程序早退并且可能引起 zerorpc 通讯中断
# 所以修改为 Ctrl+P 来终止扫描，用线程的方式，而不是出错的方式
exitControl_command = False
pauseControl_command = False

if Configuration.is_windows:
    import threading
    # 在 WSL 中可以用 pip install pypiwin32 代替部分功能
    import win32con
    import ctypes
    import ctypes.wintypes
    # pip install python_vk_codes
    # 键盘编码：https://docs.microsoft.com/en-us/windows/win32/inputdev/virtual-key-codes
    # Electron中使用Node-ffi模拟键鼠操作：https://cloud.tencent.com/developer/article/1625596

    def hotKeyMain():
        # 可以监控，退出用 CTRL-Q
        global pauseControl_command
        global exitControl_command
        user32 = ctypes.windll.user32
        cHotKeyCtrlP = 1008 # 热键的标识id
        cHotKeyCtrlQ = cHotKeyCtrlP + 1
        VK_P = 0x50
        VK_Q = 0x51
        while(True):
            if not user32.RegisterHotKey(None, cHotKeyCtrlP, win32con.MOD_CONTROL, VK_P): # Ctrl+P=暂停扫描
                Color.pl('    {!} {O}Unable to register id: %d' % cHotKeyCtrlP)
            if not user32.RegisterHotKey(None, cHotKeyCtrlQ, win32con.MOD_CONTROL, VK_Q): # Ctrl+Q=退出程序
                Color.pl('    {!} {O}Unable to register id%d' % cHotKeyCtrlQ)

            try:
                msg = ctypes.wintypes.MSG()
                if user32.GetMessageA(ctypes.byref(msg), None, 0, 0) != 0:
                    if msg.message == win32con.WM_HOTKEY:
                        if msg.wParam == cHotKeyCtrlP:
                            pauseControl_command = True
                        elif msg.wParam == cHotKeyCtrlQ:
                            exitControl_command = True
                            return
                    user32.TranslateMessage(ctypes.byref(msg))
                    user32.DispatchMessageA(ctypes.byref(msg))
            finally:
                del msg
                user32.UnregisterHotKey(None, cHotKeyCtrlP)
                user32.UnregisterHotKey(None, cHotKeyCtrlQ)

    # 监控 Ctrl+P 的线程
    class PauseHotKey(threading.Thread):
        # 来自：https://blog.csdn.net/lantuxin/article/details/82385548
        # python程序监听windows窗口热键(快捷键)
        def __init__(self, name):
            threading.Thread.__init__(self)
            self.name = name

        def run(self):
            # print ("\n***start of "+str(self.name)+"***\n")
            hotKeyMain()
            # print ("\n***end of "+str(self.name)+"***\n")

class Scanner(object):
    """ Scans wifi networks & provides menu for selecting targets """

    # Console code for moving up one line
    if Configuration.is_windows:
        UP_CHAR = '\x1B[A'
    else:
        UP_CHAR = '\033[1A'

    def __init__(self):
        self.previous_target_count = 0
        self.target_archives = {}
        self.targets = []
        self.target = None  # Target specified by user (based on ESSID/BSSID)
        self.err_msg = None
        if Configuration.is_windows:
            thread_pause_hotKey = PauseHotKey("thread_pause_hotKey")
            thread_pause_hotKey.start()

    def print_and_move_up(text):
        sys.stdout.write(f'\r{text}\x1B[A')
        sys.stdout.flush()
 
    def find_targets(self):
        """
        Scans for targets via Airodump.
        Loops until scan is interrupted via user or config.
        Sets this object `targets` attribute (list[Target]) on interruption
        """

        global pauseControl_command
        global exitControl_command
        
        max_scan_time = Configuration.scan_time

        # Loads airodump with interface/channel/etc from Configuration
        try:
            with Airodump(linux=Configuration.linux) as airodump:
                # Loop until interrupted (Ctrl+P)
                scan_start_time = time()

                while True:
                    # if airodump.pid.poll() is not None:
                    poll = Configuration.linux.poll(airodump.process.result_id)
                    if poll is not None:
                        return True  # Airodump process died

                    self.targets = airodump.get_targets(old_targets=self.targets,
                                                        target_archives=self.target_archives)

                    if self.found_target():
                        return True  # We found the target we want

                    # if airodump.pid.poll() is not None:
                    poll = Configuration.linux.poll(airodump.process.result_id)
                    if poll is not None:
                        return True  # Airodump process died

                    self.print_targets()

                    target_count = len(self.targets)
                    client_count = sum(len(t2.clients) for t2 in self.targets)

                    outline = '\r{+} Scanning'
                    if airodump.decloaking:
                        outline += ' & decloaking'
                    outline += '. Found'
                    outline += ' {G}%d{W} target(s),' % target_count
                    outline += ' {G}%d{W} client(s).' % client_count
                    outline += ' {O}Ctrl+P{W} when ready '
                    Color.clear_entire_line()
                    Color.p(outline)

                    if max_scan_time > 0 and time() > scan_start_time + max_scan_time:
                        return True

                    sleep(1)
                    if pauseControl_command or exitControl_command:
                        break

        except KeyboardInterrupt:
            return self._extracted_from_find_targets_50()
        
        if exitControl_command:
            return True
        
        if pauseControl_command:
            return self._extracted_from_find_targets_50()

    # TODO Rename this here and in `find_targets`
    def _extracted_from_find_targets_50(self):
        if not Configuration.infinite_mode:
            return True

        options = '({G}s{W}{D}, {W}{R}e{W})'
        prompt = '{+} Do you want to {G}start attacking{W} or {R}exit{W}%s?' % options

        self.print_targets()
        Color.clear_entire_line()
        Color.p(prompt)
        answer = input().lower()

        return not answer.startswith('e')

    def update_targets(self):
        """
        Archive all the old targets
        Returns: True if user wants to stop attack, False otherwise
        """
        self.previous_target_count = 0
        # for target in self.targets:
        # self.target_archives[target.bssid] = ArchivedTarget(target)

        self.targets = []
        return self.find_targets()

    def get_num_attacked(self):
        """
        Returns: number of attacked targets by this scanner
        """
        return sum(bool(target.attacked) for target in list(self.target_archives.values()))

    def found_target(self):
        """
        Detect if we found a target specified by the user (optional).
        Sets this object's `target` attribute if found.
        Returns: True if target was specified and found, False otherwise.
        """
        bssid = Configuration.target_bssid
        essid = Configuration.target_essid

        if bssid is None and essid is None:
            return False  # No specific target from user.

        for target in self.targets:
            # if Configuration.wps_only and target.wps not in [WPSState.UNLOCKED, WPSState.LOCKED]:
            #    continue
            if bssid and target.bssid and bssid.lower() == target.bssid.lower():
                self.target = target
                break
            if essid and target.essid and essid == target.essid:
                self.target = target
                break

        if self.target:
            Color.pl('\n{+} {C}found target{G} %s {W}({G}%s{W})' % (self.target.bssid, self.target.essid))
            return True

        return False

    @staticmethod
    def clr_scr():
        import platform
        import os

        cmdtorun = 'cls' if platform.system().lower() == "windows" else 'clear'
        os.system(shlex_quote(cmdtorun))

    def print_targets(self):
        """Prints targets selection menu (1 target per row)."""
        if len(self.targets) == 0:
            Color.p('\r')
            return

        if self.previous_target_count > 0 and Configuration.verbose <= 1:
            # Don't clear screen buffer in verbose mode.
            if self.previous_target_count > len(self.targets) or \
                    Scanner.get_terminal_height() < self.previous_target_count + 3:
                # Either:
                # 1) We have less targets than before, so we can't overwrite the previous list
                # 2) The terminal can't display the targets without scrolling.
                # Clear the screen.
                self.clr_scr()
            else:
                # We can fit the targets in the terminal without scrolling
                # 'Move' cursor up, so we will print over the previous list
                if Configuration.is_windows:
                    sys.stdout.write(Scanner.UP_CHAR * (2 + self.previous_target_count))
                    sys.stdout.flush()
                else:
                    Color.pl(Scanner.UP_CHAR * (3 + self.previous_target_count))

        self.previous_target_count = len(self.targets)

        # Overwrite the current line
        Color.p('\r{W}{D}')

        # First row: columns
        Color.p('   NUM')
        Color.p('                      ESSID')
        if Configuration.show_bssids:
            Color.p('              BSSID')

        if Configuration.show_manufacturers:
            Color.p('           MANUFACTURER')

        Color.pl('   CH  ENCR    PWR    WPS  CLIENT')

        # Second row: separator
        Color.p('   ---')
        Color.p('  -------------------------')
        if Configuration.show_bssids:
            Color.p('  -----------------')

        if Configuration.show_manufacturers:
            Color.p('  ---------------------')

        Color.pl('  ---  -----   ----   ---  ------{W}')

        # Remaining rows: targets
        for idx, target in enumerate(self.targets, start=1):
            Color.clear_entire_line()
            Color.p('   {G}%s  ' % str(idx).rjust(3))
            Color.pl(target.to_str(
                Configuration.show_bssids,
                Configuration.show_manufacturers
            )
            )

    @staticmethod
    def get_terminal_height():
        import os
        if Configuration.is_windows:
            rows, columns = os.get_terminal_size()
        else:
            (rows, columns) = os.popen('stty size', 'r').read().split()
        return int(rows)

    @staticmethod
    def get_terminal_width():
        import os
        if Configuration.is_windows:
            rows, columns = os.get_terminal_size()
        else:
            (rows, columns) = os.popen('stty size', 'r').read().split()
        return int(columns)

    def select_targets(self):
        """
        Returns list(target)
        Either a specific target if user specified -bssid or --essid.
        If the user used pillage or infinite attack mode retuns all the targets
        Otherwise, prompts user to select targets and returns the selection.
        """

        if self.target:
            # When user specifies a specific target
            return [self.target]

        if len(self.targets) == 0:
            if self.err_msg is not None:
                Color.pl(self.err_msg)

            # TODO Print a more-helpful reason for failure.
            # 1. Link to wireless drivers wiki,
            # 2. How to check if your device supports monitor mode,
            # 3. Provide airodump-ng command being executed.
            raise Exception('No targets found.'
                            + ' You may need to wait longer,'
                            + ' or you may have issues with your wifi card')

        # Return all targets if user specified a wait time ('pillage').
        # A scan time is always set if run in infinite mode
        if Configuration.scan_time > 0:
            return self.targets

        # Ask user for targets.
        self.print_targets()
        Color.clear_entire_line()

        if self.err_msg is not None:
            Color.pl(self.err_msg)

        input_str = '{+} Select target(s)'
        input_str += ' ({G}1-%d{W})' % len(self.targets)
        input_str += ' separated by commas, dashes'
        input_str += ' or {G}all{W}: '

        chosen_targets = []

        Color.p(input_str)
        for choice in input().split(','):
            choice = choice.strip()
            if choice.lower() == 'all':
                chosen_targets = self.targets
                break
            if '-' in choice:
                # User selected a range
                (lower, upper) = [int(x) - 1 for x in choice.split('-')]
                for i in range(lower, min(len(self.targets), upper + 1)):
                    chosen_targets.append(self.targets[i])
            elif choice.isdigit():
                choice = int(choice)
                if choice > len(self.targets):
                    Color.pl('    {!} {O}Invalid target index (%d)... ignoring' % choice)
                    continue

                chosen_targets.append(self.targets[choice - 1])

        return chosen_targets


if __name__ == '__main__':
    # 'Test' script will display targets and selects the appropriate one
    Configuration.initialize()
    targets = []
    try:
        s = Scanner()
        s.find_targets()
        targets = s.select_targets()
    except Exception as e:
        Color.pl('\r {!} {R}Error{W}: %s' % str(e))
        Configuration.exit_gracefully()
    for t in targets:
        Color.pl('    {W}Selected: %s' % t)
    Configuration.exit_gracefully()

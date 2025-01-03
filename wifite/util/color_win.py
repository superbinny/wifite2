#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ctypes, sys

# Console colors
N = '\033[m'  # NONE
W = '\033[0m'  # white (normal)
R = '\033[31m'  # red
LR = '\033[1;31m'  # LIGHT_RED
G = '\033[32m'  # green
LG = '\033[1;32m'  # LIGHT_GREEN
O = '\033[33m'  # orange
B = '\033[34m'  # blue
LB = '\033[1;34m'  # LIGHT_BLUE
P = '\033[35m'  # purple
LP = '\033[1;35m'  # LIGHT_PURPLE
C = '\033[36m'  # cyan
LC = '\033[1;36;43m'  # LIGHT_CYAN
GR = '\033[37m'  # gray
DG = '\033[1;30m'  # DARY_GRAY
Y = '\033[1;33m' # YELLOW
D = '\033[2m' # dims current color. {W} resets.

# define NONE         "\033[m"
# define RED          "\033[0;32;31m"
# define LIGHT_RED    "\033[1;31m"
# define GREEN        "\033[0;32;32m"
# define LIGHT_GREEN  "\033[1;32m"
# define BLUE         "\033[0;32;34m"
# define LIGHT_BLUE   "\033[1;34m"
# define DARY_GRAY    "\033[1;30m"
# define CYAN         "\033[0;36m"
# define LIGHT_CYAN   "\033[1;36;43m"
# define PURPLE       "\033[0;35m"
# define LIGHT_PURPLE "\033[1;35m"
# define BROWN        "\033[0;33m"
# define YELLOW       "\033[1;33m"
# define LIGHT_GRAY   "\033[0;37m"
# define WHITE        "\033[1;37m"

class Color:
    is_windows = sys.platform == 'win32'
    """ Helper object for easily printing colored text to the terminal. """
    # Basic console colors
    colors_linux = {
        'W': '\033[0m',   # white (normal)
        'R': '\033[31m',  # red
        'G': '\033[32m',  # green
        'O': '\033[33m',  # orange
        'B': '\033[34m',  # blue
        'P': '\033[35m',  # purple
        'C': '\033[36m',  # cyan
        'GR': '\033[37m',  # gray
        'D': '\033[2m'    # dims current color. {W} resets.
    }

    
    # Helper string replacements
    replacements = {
            '{+}': ' {W}{D}[{W}{G}+{W}{D}]{W}',
                '{!}': ' {O}[{R}!{O}]{W}',
                '{?}': ' {W}[{C}?{W}]'
        }
    
    last_sameline_length = 0
    
    if is_windows:
        STD_INPUT_HANDLE = -10
        STD_OUTPUT_HANDLE = -11
        STD_ERROR_HANDLE = -12
    
        # 字体颜色定义 ,关键在于颜色编码，由2位十六进制组成，分别取0~f，前一位指的是背景色，后一位指的是字体色
        # 由于该函数的限制，应该是只有这16种，可以前景色与背景色组合。也可以几种颜色通过或运算组合，组合后还是在这16种颜色中
    
        # Windows CMD命令行 字体颜色定义 text colors
        FOREGROUND_BLACK = 0x00  # black.
        FOREGROUND_DARKBLUE = 0x01  # dark blue.
        FOREGROUND_DARKGREEN = 0x02  # dark green.
        FOREGROUND_DARKSKYBLUE = 0x03  # dark skyblue.
        FOREGROUND_DARKRED = 0x04  # dark red.
        FOREGROUND_DARKPINK = 0x05  # dark pink.
        FOREGROUND_DARKYELLOW = 0x06  # dark yellow.
        FOREGROUND_DARKWHITE = 0x07  # dark white.
        FOREGROUND_DARKGRAY = 0x08  # dark gray.
        FOREGROUND_BLUE = 0x09  # blue.
        FOREGROUND_GREEN = 0x0a  # green.
        FOREGROUND_SKYBLUE = 0x0b  # skyblue.
        FOREGROUND_RED = 0x0c  # red.
        FOREGROUND_PINK = 0x0d  # pink.
        FOREGROUND_YELLOW = 0x0e  # yellow.
        FOREGROUND_WHITE = 0x0f  # white.
    
        FOREGROUND_INTENSITY = 0x08  # text color is intensified.
    
        # Windows CMD命令行 背景颜色定义 background colors
        BACKGROUND_BLUE = 0x10  # dark blue.
        BACKGROUND_GREEN = 0x20  # dark green.
        BACKGROUND_DARKSKYBLUE = 0x30  # dark skyblue.
        BACKGROUND_DARKRED = 0x40  # dark red.
        BACKGROUND_DARKPINK = 0x50  # dark pink.
        BACKGROUND_DARKYELLOW = 0x60  # dark yellow.
        BACKGROUND_DARKWHITE = 0x70  # dark white.
        BACKGROUND_DARKGRAY = 0x80  # dark gray.
        BACKGROUND_BLUE = 0x90  # blue.
        BACKGROUND_GREEN = 0xa0  # green.
        BACKGROUND_SKYBLUE = 0xb0  # skyblue.
        BACKGROUND_RED = 0xc0  # red.
        BACKGROUND_PINK = 0xd0  # pink.
        BACKGROUND_YELLOW = 0xe0  # yellow.
        BACKGROUND_WHITE = 0xf0  # white.
    
        BACKGROUND_INTENSITY = 0x80  # background color is intensified.
    
        # get handle
        std_out_handle = ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
    
    @classmethod
    def __init__(cls):
        # Basic console colors
        cls.colors = {
                'W': [W, cls.printWhite],  # white (normal)
                    'R': [R, cls.printRed],  # red
                    'G': [G, cls.printGreen],  # green
                    'LG': [LG, cls.printDarkGreen],  # light green
                    'O': [O, cls.printYellow],  # orange
                    'B': [B, cls.printBlue],  # blue
                    'P': [P, cls.printPink],  # purple
                    'C': [C, cls.printDarkPink],  # cyan
                    'GR': [GR, cls.printDarkGray],  # gray
                    'D': [D, cls.printDarkGray]  # dims current color. {W} resets.
            }
        
    @classmethod
    def set_cmd_text_color(cls, color, handle=None):
        if handle is None:
            handle = cls.std_out_handle
        bool_ret = ctypes.windll.kernel32.SetConsoleTextAttribute(handle, color)
        return bool_ret

    # reset white
    @classmethod
    def resetColor(cls):
        cls.set_cmd_text_color(cls.FOREGROUND_RED | cls.FOREGROUND_GREEN | cls.FOREGROUND_BLUE)
        
    ###############################################################
    @classmethod
    def printMessage(cls, color, mess):
        cls.set_cmd_text_color(color)
        sys.stdout.write(mess)
        sys.stdout.flush()
        cls.resetColor()

    # 暗蓝色
    # dark blue
    @classmethod
    def printDarkBlue(cls, mess):
        if cls.is_windows:
            cls.printMessage(cls.FOREGROUND_DARKBLUE, mess)
        else:
            cls.pl(B + mess, isend=False)

    # 暗绿色
    # dark green
    @classmethod
    def printDarkGreen(cls, mess):
        if cls.is_windows:
            cls.printMessage(cls.FOREGROUND_DARKGREEN, mess)
        else:
            cls.pl(G + mess, isend=False)

    # 亮绿色
    # light green
    @classmethod
    def printLightGreen(cls, mess):
        if cls.is_windows:
            cls.printMessage(cls.FOREGROUND_GREEN |
                              cls.FOREGROUND_INTENSITY, mess)
        else:
            cls.pl(LG + mess, isend=False)

    # 暗天蓝色
    # dark sky blue
    @classmethod
    def printDarkSkyBlue(cls, mess):
        if cls.is_windows:
            cls.printMessage(cls.FOREGROUND_DARKSKYBLUE, mess)
        else:
            cls.pl(B + mess, isend=False)

    # 暗红色
    # dark red
    @classmethod
    def printDarkRed(cls, mess):
        if cls.is_windows:
            cls.printMessage(cls.FOREGROUND_DARKRED, mess)
        else:
            cls.pl(R + mess, isend=False)
    
    @classmethod
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

    # 暗粉红色
    # dark pink
    @classmethod
    def printDarkPink(cls, mess):
        try:
            if cls.is_windows:
                cls.printMessage(cls.FOREGROUND_DARKPINK, mess)
            else:
                cls.pl(C + mess, isend=False)
        except UnicodeEncodeError:
            print('UnicodeEncodeError: %s' % cls.bnStr2Hex(mess))

    # 暗黄色
    # dark yellow
    @classmethod
    def printDarkYellow(cls, mess):
        if cls.is_windows:
            cls.printMessage(cls.FOREGROUND_DARKYELLOW, mess)
        else:
            cls.pl(Y + mess, isend=False)

    # 暗白色
    # dark white
    @classmethod
    def printDarkWhite(cls, mess):
        if cls.is_windows:
            cls.printMessage(cls.FOREGROUND_DARKWHITE, mess)
        else:
            cls.pl(B + mess, isend=False)

    # 暗灰色
    # dark gray
    @classmethod
    def printDarkGray(cls, mess):
        if cls.is_windows:
            cls.printMessage(cls.FOREGROUND_DARKGRAY, mess)
        else:
            cls.pl(DG + mess, isend=False)

    # 蓝色
    # blue
    @classmethod
    def printBlue(cls, mess):
        if cls.is_windows:
            cls.printMessage(cls.FOREGROUND_BLUE, mess)
        else:
            cls.pl(LB + mess, isend=False)

    # 绿色
    # green
    @classmethod
    def printGreen(cls, mess):
        if cls.is_windows:
            cls.printMessage(cls.FOREGROUND_GREEN, mess)
        else:
            cls.pl(LG + mess, isend=False)

    # 天蓝色
    # sky blue
    @classmethod
    def printSkyBlue(cls, mess):
        if cls.is_windows:
            cls.printMessage(cls.FOREGROUND_SKYBLUE, mess)
        else:
            cls.pl(LB + mess, isend=False)

    # 红色
    # red
    @classmethod
    def printRed(cls, mess):
        if cls.is_windows:
            cls.printMessage(cls.FOREGROUND_RED, mess)
        else:
            cls.pl(LR + mess, isend=False)

    # 粉红色
    # pink
    @classmethod
    def printPink(cls, mess):
        if cls.is_windows:
            cls.printMessage(cls.FOREGROUND_PINK, mess)
        else:
            cls.pl(LC + mess, isend=False)

    # 黄色
    # yellow
    @classmethod
    def printYellow(cls, mess):
        if cls.is_windows:
            cls.printMessage(cls.FOREGROUND_YELLOW, mess)
        else:
            cls.pl(Y + mess, isend=False)

    # 白色
    # white
    @classmethod
    def printWhite(cls, mess):
        if cls.is_windows:
            cls.printMessage(cls.FOREGROUND_WHITE, mess)
        else:
            cls.pl(W + mess, isend=False)

    ##################################################

    # 白底黑字
    # white bkground and black text
    @classmethod
    def printWhiteBlack(cls, mess):
        if cls.is_windows:
            cls.printMessage(cls.FOREGROUND_BLACK |
                              cls.BACKGROUND_WHITE, mess)
        else:
            cls.pl(R + mess, isend=False)

    # 白底黑字
    # white bkground and black text
    @classmethod
    def printWhiteBlack_2(cls, mess):
        if cls.is_windows:
            cls.printMessage(0xf0, mess)
        else:
            cls.pl(R + mess, isend=False)

    # 黄底蓝字
    # white bkground and black text
    def printYellowRed(cls, mess):
        if cls.is_windows:
            cls.printMessage(cls.BACKGROUND_YELLOW |
                              cls.FOREGROUND_RED, mess)
        else:
            cls.pl(R + mess, isend=False)
            
    @classmethod
    def p(cls, text):
        """
        Prints text using colored format on same line.
        Example:
            cls.p('{R}This text is red. {W} This text is white')
        """
        sys.stdout.write(cls.s(text))
        sys.stdout.flush()
        if '\r' in text:
            text = text[text.rfind('\r') + 1:]
            cls.last_sameline_length = len(text)
        else:
            cls.last_sameline_length += len(text)

    @classmethod
    def pl(cls, text, isend=True):
        """Prints text using colored format with trailing new line."""
        if cls.is_windows:
            # convert to linux
            text = cls.s(text)
            msg_lst = text.split('\033')
            if len(msg_lst) > 0:
                for m in msg_lst:
                    if len(m):
                        test_msg = '\033' + m
                        Find = False
                        for key in cls.colors.keys():
                            if len(test_msg) >= len(cls.colors[key][0]):
                                if cls.colors[key][0] == test_msg[:len(cls.colors[key][0])]:
                                    msg_normal = test_msg[len(cls.colors[key][0]):]
                                    if len(msg_normal):
                                        # print("%s:%s" % (key, getattr(cls.colors[key][1], '__name__')))
                                        cls.colors[key][1](msg_normal)
                                    Find = True
                                    break
                        if not Find:
                            cls.printWhite(m)
                if isend:
                    cls.printWhite('\n')
            else:
                print(text)
        else:
            cls.p('%s\n' % text)
            
        cls.last_sameline_length = 0

    @classmethod
    def pe(cls, text):
        """
        Prints text using colored format with
        leading and trailing new line to STDERR.
        """
        sys.stderr.write(cls.s('%s\n' % text))
        cls.last_sameline_length = 0

    @classmethod
    def s(cls, text):
        """ Returns colored string """
        output = text
        for (key, value) in list(cls.replacements.items()):
            output = output.replace(key, value)
        for (key, value) in list(cls.colors_linux.items()):
            output = output.replace('{%s}' % key, value)
        return output


    @classmethod
    def clear_line(cls):
        spaces = ' ' * cls.last_sameline_length
        sys.stdout.write('\r%s\r' % spaces)
        sys.stdout.flush()
        cls.last_sameline_length = 0

    @classmethod
    def clear_entire_line(cls):
        import os
        if cls.is_windows:
            rows, columns = os.get_terminal_size()
        else:
            (rows, columns) = os.popen('stty size', 'r').read().split()
        cls.p('\r' + (' ' * int(columns)) + '\r')

    @classmethod
    def pattack(cls, attack_type, target, attack_name, progress):
        """
        Prints a one-liner for an attack.
        Includes attack type (WEP/WPA),
        target ESSID & power, attack type, and progress.
        ESSID (Pwr) Attack_Type: Progress
        e.g.: Router2G (23db) WEP replay attack: 102 IVs
        """
        essid = '{C}%s{W}' % target.essid if target.essid_known else '{O}unknown{W}'
        cls.p('\r{+} {G}%s{W} ({C}%sdb{W}) {G}%s {C}%s{W}: %s ' % (
            essid, target.power, attack_type, attack_name, progress))

    @classmethod
    def pexception(cls, exception, call_from=None):
        """Prints an exception. Includes stack trace if necessary."""
        if call_from is None:
            _call_from = ''
        else:
            _call_from = f',From:{call_from}'
            
        cls.pl('\n{!} {R}Error: {O}%s%s' % (str(exception), _call_from))

        # Don't dump trace for the "no targets found" case.
        if 'No targets found' in str(exception):
            return

        from ..config_win import Configuration
        if Configuration.verbose > 0 or Configuration.print_stack_traces:
            cls.pl('\n{!} {O}Full stack trace below')
            from traceback import format_exc
            cls.p('\n{!}    ')
            err = format_exc().strip()
            err = err.replace('\n', '\n{!} {C}   ')
            err = err.replace('  File', '{W}File')
            err = err.replace('  Exception: ', '{R}Exception: {O}')
            cls.pl(err)

# 自动实例化
instance = Color()
 
# 控制导入时自动实例化的对象
__all__ = ['instance']

if __name__ == '__main__':
    Color.pl('{R}Testing{G}One{C}Two{P}Three{W}Done')
    print((Color.s('{C}Testing{P}String{W}')))
    Color.pl('{+} Good line')
    Color.pl('{!} Danger')

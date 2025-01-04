#!/usr/bin/env python
# -*- coding: utf-8 -*-
# *********************************************************
#       Created:     2025-1-2   10:00
#       Filename:    brute_force.py
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
#       Purpose:     暴力破解 wifi
#       Copyright:   TJYM(C) 2014 - All Rights Reserved
#       LastModify:  2025-1-2
# *********************************************************


from ..model.attack_win import Attack
from ..util.color_win import Color
from ..config_win import Configuration
import pywifi

class AttackBruteForce(Attack):
    @staticmethod
    def can_attack_bruteforce():
        return True

    def __init__(self, target, pixie_dust=False, null_pin=False):
        super(AttackBruteForce, self).__init__(target)
        self.success = False
        self.crack_result = None

    def run(self):
        return self.run_bruteforce()

    def run_bruteforce(self):
        return self.success

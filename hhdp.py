#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys


class DoIt(object):
    def __init__(self, hosts_file, args):
        self.hosts = hosts_file
        self.args = args
        self.__args_check()

    def __args_check(self):
        if not os.path.isfile(self.hosts):
            sys.stdout.write("%s no such file\n" % self.hosts)
            sys.exit(1)

    def run(self):
        print(self.args)
        print(self.hosts)

if __name__ == '__main__':
    instance = DoIt('/etc/hosts_list', sys.argv)
    instance.run()

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys


class Base(object):
    def __init__(self, hosts_file, args):
        self.hosts_file = hosts_file
        self.args = args
        self.hosts = self.__gen_list()

    def __gen_list(self):
        hosts_list = []
        file_content = open(self.hosts_file, "r")
        file_list = file_content.readlines()
        for line in file_list:
            if line[0] == '#':
                continue
            line = line.split()
            kv = dict()
            for i in line:
                h = i.split(':')
                kv[h[0]] = h[1]
            hosts_list.append(kv)
        return hosts_list

    def run(self):
        print(self.args)
        print(self.hosts_file)


class DoIt(object):
    def __init__(self, hosts_file, args):
        self.hosts_file = hosts_file
        self.args = args

    def __args_check(self):
        if not os.path.isfile(self.hosts_file):
            sys.stdout.write("%s no such file\n" % self.hosts_file)
            sys.exit(1)

    def run(self):
        base = Base(self.hosts_file, self.args)
        base.run()
        if base.hosts:
            print base.hosts
            print len(base.hosts)
        else:
            print('no such valid line')

if __name__ == '__main__':
    instance = DoIt('./hosts_list', sys.argv)
    instance.run()
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys


class Base(object):
    def __init__(self, hosts_file, args):
        self.hosts_file = hosts_file
        self.args = args
        self.hosts = self.__gen_dict()

    def __gen_dict(self):
        hosts_dict = {}
        line_id = 0
        file_content = open(self.hosts_file, "r")
        file_list = file_content.readlines()
        for line in file_list:
            if line[0] == '#':
                continue
            line_id = int(line_id) + 1
            dict_key = 'node_' + str(line_id)
            line = line.split()
            for i in line:
                try:
                    type(hosts_dict[dict_key])
                except KeyError:
                    hosts_dict[dict_key] = {}
                h = i.split(':')
                hosts_dict[dict_key][h[0]] = h[1]
        return hosts_dict

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
        else:
            print('no such valid line')

if __name__ == '__main__':
    instance = DoIt('/etc/hosts_list', sys.argv)
    instance.run()

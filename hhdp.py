#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys


class Base(object):
    def __init__(self, hosts_file, args):
        self.hosts_file = hosts_file
        self.args = args
        self.hosts = self.__gen_list()

    @staticmethod
    def kev_value_check(_list):
        if not len(_list):
            return 1
        new_list = []
        for line in _list:
            print line
            new_list.append(line)
        return new_list

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
        return Base.kev_value_check(hosts_list)

    def run(self):
        print(self.hosts_file)


class DoIt(object):
    def __init__(self, hosts_file, args):
        self.hosts_file = hosts_file
        self.args = args
        self.size = len(args)
        self.__args_check()

    def __help_docs(self):
        n = self.args[0]
        sys.stdout.write("""Usage: %s [options] params

        Options:
          -h : show this help message and exit
          -c [shell commands] : execute command on each node
          -f [source|target] : sync file or directory to every node

        Example:
          -c :
            Exam_1 :
              %s -c hostname
            Exam_2 :
              %s -c 'ip a|grep -q net && echo ok ||echo no'

          -f : [local node] => [other node]
            Exam_1 : file path same on local and remote
              %s -f /opt/file
            Exam_2 : file path different on local and remote
              %s -f /opt/file1 /opt/file2
            Exam_3 : dir path same on local and remote
              %s -f /opt/dir
            Exam_4 : dir path different on local and remote
              %s -f /opt/dir1 /opt/dir2
        """ % (n, n, n, n, n, n, n))

    def __args_check(self):
        if not os.path.isfile(self.hosts_file):
            sys.stdout.write("%s no such file\n" % self.hosts_file)
            sys.exit(1)
        if self.args[1] == "-c":
            if self.size == 2:
                print("hostname")
            elif self.size == 3:
                print(self.args[2])
            else:
                self.__help_docs()
        elif self.args[1] == "-f":
            sync_path = self.args[2:]
            if self.size == 4:
                print(sync_path)
            elif self.size == 3:
                sync_path.append(sync_path[0])
                print(sync_path)
            else:
                self.__help_docs()
        elif self.args[0] == "-h":
            self.__help_docs()
        else:
            self.__help_docs()

    def run(self):
        base = Base(self.hosts_file, self.args)
        base.run()
        if base.hosts:
            print base.hosts
        else:
            print('no such valid line')

if __name__ == '__main__':
    instance = DoIt('./hosts_list', sys.argv)
    instance.run()
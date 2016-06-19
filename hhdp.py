#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys


class Base(object):
    def __init__(self, hosts_file, args):
        self.hosts_file = hosts_file
        self.args = args
        self.size = len(args)
        self.params = self.__args_check()
        self.map_list = self.__gen_list()

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
        \n""" % (n, n, n, n, n, n, n))
        sys.exit(1)

    def kev_value_check(self, _list):
        if not len(_list):
            return
        default_kv = {
            "port": "22",
            "user": "root",
            "passwd": "key",
            "pkey": "/opt/pro/id_rsa"

        }
        new_list = []
        for line in _list:
            if "port" not in line:
                line["port"] = default_kv["port"]
            if "user" not in line:
                line["user"] = default_kv["user"]
            if "passwd" not in line:
                line["passwd"] = default_kv["passwd"]
            if "pkey" not in line:
                line["pkey"] = default_kv["pkey"]
            if "ip" in line:
                line = dict(line, **self.params)
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
        return self.kev_value_check(hosts_list)

    def __args_check(self):
        if not os.path.isfile(self.hosts_file):
            sys.stdout.write("%s no such file\n" % self.hosts_file)
            self.__help_docs()
        _args = {}
        if self.args[1] == "-c":
            if self.size == 2:
                _args["cmd"] = "hostname"
            elif self.size == 3:
                _args["cmd"] = self.args[2]
            else:
                self.__help_docs()
        elif self.args[1] == "-f":
            if self.size == 4:
                _args = Tools.check_path(self.args[2], self.args[3])
            elif self.size == 3:
                _args = Tools.check_path(self.args[2], self.args[2])
            else:
                self.__help_docs()
        if not len(_args):
            self.__help_docs()
        return _args


class DoIt(object):
    def __init__(self, _map):
        self.map = _map
        self.ip = _map["ip"]
        self.port = _map["port"]
        self.user = _map["user"]
        self.passwd = _map["passwd"]
        self.pkey = _map["pkey"]


class Tools(object):
    @staticmethod
    def check_dir(_dir):
        if _dir[-1] != '/':
            return _dir + '/'
        else:
            return _dir

    @staticmethod
    def check_path(_src, _dst):
        _res = {}
        if os.path.isfile(_src) and _dst[-1] != "/":
            _res["src"] = _src
            _res["dst"] = _dst
        elif os.path.isdir(_src):
            _res["src"] = Tools.check_dir(_src)
            _res["dst"] = Tools.check_dir(_dst)
        return _res


if __name__ == '__main__':
    instance = Base('./hosts_list', sys.argv)
    if instance.map_list:
        print(instance.map_list)
    else:
        print("no such vaild line")
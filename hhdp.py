#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import paramiko

from subprocess import Popen, PIPE
from time import strftime, localtime
from threading import Thread, Lock
from Queue import Queue
from pexpect import run as prun


class Base(object):
    """ 基础类.

    此类的作用为读取列表文件,确认有效性行,生成一个列表.

    属性:
        hosts_file: 列表文件路径.
        args: 传递进来的所有命令行参数.
        size: 传递进来的命令行参数的个数(空格分割).
        params: 具体使用的有效参数.
        map_list: 列表文件最终会生成的有效列表数据.
    """
    def __init__(self, hosts_file, args):
        self.hosts_file = hosts_file
        self.args = args
        self.size = len(args)
        self.params = self.__args_check()
        self.map_list = self.__gen_list()

    def __help_docs(self):
        """ 帮助文档,参数不识别或错误时执行. """
        n = self.args[0]
        sys.stdout.write("""Usage: %s [options] params

        Options:
          -h : show this help message and exit
          -c [shell commands] : execute command on each remote node
          -f [source|target] : sync file or directory to each remote node

        Example:
          -c :
            Exam_1 :
              %s -c hostname
            Exam_2 :
              %s -c 'ip a|grep -q net && echo ok ||echo no'

          -f : [local node] => [each remote node]
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
        """ 列表完整性处理方法.

        此方法将已经根据列表文件生成的列表数据中的默认值补全.

        Arg:
            _list: 原始列表数据.

        Return:
            补全后的完成列表.
        """
        if not len(_list):
            return
        default_kv = {
            "port": "22",
            "user": "root",
            "passwd": "key",
            "pkey": "/root/.ssh/id_rsa"
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
                if line["passwd"] == "key" and not os.path.isfile(line["pkey"]):
                    print("Warn, %s %s no such file" % (line["ip"], line["pkey"]))
                    continue
                line = dict(line, **self.params)
                new_list.append(line)
        return new_list

    def __gen_list(self):
        """ 读取列表文件生成一个有效列表变量并返回. """
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
        if not len(hosts_list):
            print("No such valid line in the %s" % self.hosts_file)
            self.__help_docs()
        return self.kev_value_check(hosts_list)

    def __args_check(self):
        """ 检查参数,并返回处理后的有效参数,参数无效时输出帮助并退出. """
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
    """ 工作类.

    此类接收一个dict变量,根据其中的有效关键字和值,
    进行命令或文件的同步动作.

    属性:
        _map: 一个包含有足够信息的字典,
        此字典变量应该包含的信息应为如下两种:
            1. {
                "ip":"ip或主机名",
                "port":"端口",
                "user":"用户名",
                "passwd":"密码",
                "pkey": "ssh私钥路径",
                "cmd": "命令行传递的shell命令"
                }
            2. {
                "ip":"ip或主机名",
                "port":"端口",
                "user":"用户名",
                "passwd":"密码",
                "pkey": "ssh私钥路径",
                "src": "命令行-f后面,以空格隔开的第一个路径",
                "dst": "命令行-f后面,以空格隔开的第二个路径,如果无则为第一个路径"
                }
    """
    _output_lock = Lock()   # 标准输出锁,并发时,不加锁会导致屏幕输出混乱

    def __init__(self, _map):
        self.map = _map
        self.ip = _map["ip"]
        self.port = int(_map["port"])
        self.user = _map["user"]
        self.passwd = _map["passwd"]
        self.pkey = _map["pkey"]

    @staticmethod
    def _output(_msg):
        """ 用于给标准输出加锁的方法, 线程任务输出时应调用此方法. """
        if DoIt._output_lock.acquire():
            sys.stdout.write(_msg)
            DoIt._output_lock.release()

    def cmd_ctrl(self):
        """ 命令执行方法. """
        ssh_conn = paramiko.SSHClient()
        ssh_conn.load_system_host_keys()
        ssh_conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if self.passwd == "key":
            load_key = paramiko.RSAKey.from_private_key_file(self.pkey)
            try:
                ssh_conn.connect(self.ip, self.port, self.user, pkey=load_key)
            except paramiko.SSHException:
                self._output("%s ssh connect failed\n" % self.ip)
                return
        else:
            try:
                ssh_conn.connect(self.ip, self.port, self.user, self.passwd)
            except paramiko.SSHException:
                self._output("%s ssh connect failed\n" % self.ip)
                return
        stdin, stdout, stderr = ssh_conn.exec_command(str(self.map["cmd"]))
        self._output(stdout.read() + stderr.read())
        ssh_conn.close()

    @staticmethod
    def sync_ctrl_fail_info(_code, _info="Nothing", _start="Nothing"):
        """ 文件同步方法的输出方法(复用和加锁). """
        if DoIt._output_lock.acquire():
            if int(_code) == 0:
                sys.stdout.write("%s %s ok\n" % (_start, Tools.now_time()))
            else:
                sys.stdout.write("%s %s failed\n" % (_start, Tools.now_time()))
                sys.stdout.write(_info + "\n")
            DoIt._output_lock.release()

    def sync_ctrl(self):
        """ 文件同步方法. """
        _user = self.user
        _ip = self.ip
        _src = self.map["src"]
        _dst = self.map["dst"]
        _start = "%s => %s:%s %s ->" % (_src, self.ip, _dst, Tools.now_time())
        _cmd = "/usr/bin/rsync -a -e"
        if self.passwd == "key":
            _args = '"ssh -p %s -i %s -q -o StrictHostKeyChecking=no"' % (self.port, self.pkey)
            sync_cmd = Popen("%s %s %s %s@%s:%s" % (_cmd, _args, _src, _user, _ip, _dst), shell=True, stderr=PIPE)
            sync_cmd.wait()
            self.sync_ctrl_fail_info(sync_cmd.returncode, sync_cmd.stderr.read(), _start)
        else:
            _args = '"ssh -p %s -q -o StrictHostKeyChecking=no"' % self.port
            _command = '%s %s %s %s@%s:%s' % (_cmd, _args, _src, _user, _ip, _dst)
            (_output, _return_code) = prun(_command, withexitstatus=True, events={'password': '%s\n' % self.passwd})
            self.sync_ctrl_fail_info(_return_code, _output, _start)

    def run(self):
        """ 启动方法. """
        if "cmd" in self.map:
            self.cmd_ctrl()
        elif "src" in self.map:
            self.sync_ctrl()
        else:
            self._output(self.ip + " do nothing!\n")
            return


class WorkManager(object):
    """线程池管理类.

    用于初始化有效队列长度,线程池大小,
    并等待线程结束.

    属性:
        base: 基础类(Base)的实例对象
        work_queue: 初始化一个长度为0的队列.
        threads: 具体工作线程的列表.
        thread_pool_size: 工作线程池的大小.
    """
    def __init__(self, base_object, threads=5):
        self.base = base_object
        self.threads = threads
        self.work_queue = Queue()
        self.threads_list = []
        self.thread_pool_size = self.__thread_pool_size()
        self.__init_work_queue()
        self.__init_thread_pool()

    def __thread_pool_size(self):
        """简单计算需要线程池大小方法.

        如果当前有效上传列表的行数大于或登陆配置文件中线程数量,
        则以配置文件中的线程数量为准; 反之,则使用上传列表的个数
        为并发上传的个数.

        Return:
            返回一个大于0的有效数字.
        """
        list_len = len(self.base.map_list)
        if list_len >= self.threads:
            return self.threads
        else:
            return list_len

    def __init_thread_pool(self):
        """ 初始化工作线程池. """
        for i in range(self.thread_pool_size):
            self.threads_list.append(Work(self.work_queue, self.base))

    def __init_work_queue(self):
        """ 初始化有效队列总长度. """
        for i in self.base.map_list:
            self.add_job(self.job, i)

    def add_job(self, func, arg):
        """添加具体任务方法到处理队列.

        Args:
            func: 具体执行任务的方法.
            arg: 具体执行任务方法所需参数.
        """
        self.work_queue.put((func, arg))

    @staticmethod
    def job(_line):
        """执行具体的任务.

        其实就是把上传列表遍历并传递给DfsCtrl的对象.

        Args:
            _line: 当前需要处理的行.
        """
        up_thread = DoIt(_line)
        up_thread.run()

    def check_queue(self):
        """检查队列长度.

        Return:
            返回当前队列的有效长度.
        """
        return self.work_queue.qsize()

    def wait_all_complete(self):
        """ 等待所有队列完成. """
        for i in self.threads_list:
            if i.isAlive():
                i.join()


class Work(Thread):
    """工作类.

    线程池的某个线程的工作过程控制, 譬如thread-n;
    每执行完成当前任务, 就会被再次问队列取一个再次执行.

    属性:
        _thread_lock: 线程锁,获取新任务时避免可能产生的竞争问题.
        base: 引用基础类的实例化对象
        work_queue: 任务队列总长度
    """
    _thread_lock = Lock()

    def __init__(self, work_queue, base_object):
        Thread.__init__(self)
        self.base = base_object
        self.work_queue = work_queue
        self.start()

    def run(self):
        """ 执行任务直到队列为空. """
        while True:
            if Work._thread_lock.acquire():
                if self.work_queue.empty():
                    Work._thread_lock.release()
                    break
                do, args = self.work_queue.get(False)
                Work._thread_lock.release()
                do(args)
                self.work_queue.task_done()


class Tools(object):
    @staticmethod
    def now_time():
        """ 返回固定格式的当前时间. """
        return strftime("%Y/%m/%d %H:%M:%S", localtime())

    @staticmethod
    def check_dir(_dir):
        """ 确保路径的最后一个字符串为斜杠并返回. """
        if _dir[-1] != '/':
            return _dir + '/'
        else:
            return _dir

    @staticmethod
    def check_path(_src, _dst):
        """ 确认本地和远程路径的有效性.

        Arg:
            _src: 本地路径
            _dst: 远程路径
        Return:
            返回一个字典变量,其中包含两个有效的键: src 和 dst.
        """
        _res = {}
        if os.path.isfile(_src) and _dst[-1] != "/":
            _res["src"] = _src
            _res["dst"] = _dst
        elif os.path.isdir(_src):
            _res["src"] = Tools.check_dir(_src)
            _res["dst"] = Tools.check_dir(_dst)
        return _res


if __name__ == '__main__':
    instance = Base('/etc/hosts_list', sys.argv)
    work_manager = WorkManager(instance, 8)
    work_manager.wait_all_complete()


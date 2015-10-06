#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys, getopt, getpass, ConfigParser
import paramiko, threading, pexpect, subprocess
from time import strftime, localtime

def usage():
  """ 帮助文档 """
  print '''Usage: hhdp [options] params

Options:
  -h, --help                     show this help message and exit
  -i, --install                  show required package 
  -c, --command [comannd_names]  execute command on each node 
  -f, --file [SRC|DEST]          sync file or directory to every node
  
Example:
  -c : 
    Exam_1 : 
      hhdp -c hostname
    Exam_2 :
      hhdp -c 'ip a|grep -q net && echo ok ||echo no'

  -f : [local node] => [other node]
    Exam_1 : file path same on local and remote
      hhdp -f /opt/file
    Exam_2 : file path different on local and remote
      hhdp -f '/opt/file1 /opt/file2'
    Exam_3 : dir path same on local and remote 
      hhdp -f /opt/dir
    Exam_4 : dir path different on local and remote
      hhdp -f '/opt/dir1 /opt/dir2'
'''


def installPackage():
  """ 安装依赖包说明 """
  package = 'python-paramiko python-iniparse python-crypto python-pexpect'
  print '''## You need to install some package before using it.

## Ubuntu:
apt-get -y install %s

## Redhat/CentOS:
yum -y install %s ''' % (package, package)


def hostsHash(hosts_file):
  """ 将传递进来的hosts规则文件内容转换成字典后return """
  hosts_dict = {}
  line_id = 0
  if os.path.isfile(hosts_file):
    file_content = open(hosts_file, "r")
    file_list = file_content.readlines()
    for line in file_list:
      line_id = int(line_id) + 1
      dict_key = 'node_' + str(line_id)
      line = line.split()
      for t in line:
        hosts_dict[dict_key] = {}
      for i in line:
        h = i.split(':')     
        hosts_dict[dict_key][h[0]] = h[1]
    return hosts_dict
  else:
    print "%s no such file" % hosts_file
    sys.exit(2)

def cmdRun(cmd, ip, port, user, passwd, pkey):
  """ 根据参数执行命令 """
  s = paramiko.SSHClient()
  s.load_system_host_keys()
  s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
  if passwd == 'key':
    if os.path.isfile(pkey):
      key = paramiko.RSAKey.from_private_key_file(pkey)
      s.connect(ip, port, user, pkey=key)
    else:
      print "%s no such file" % pkey
      sys.exit(3)
  else:
    s.connect(ip, port, user, passwd)
  stdin, stdout, stderr = s.exec_command(str(cmd))
  print stdout.read(),
  s.close()

def cmdRoute(cmd, hosts_dict):
  """ 将传递进来的命令应用到传递进来字典的每个ip """
  threads = []
  for key in hosts_dict:
    port = 22
    user = getpass.getuser()
    passwd = 'key' 
    pkey = os.environ['HOME'] + '/.ssh/id_rsa'
    for k in hosts_dict[key]:
      if k == 'ip':
        ip = hosts_dict[key][k]
      elif k == 'port':
        port = int(hosts_dict[key][k])
      elif k == 'user':
        user = hosts_dict[key][k]
      elif k == 'passwd':
        passwd = hosts_dict[key][k]
      elif k == 'pkey':
        pkey = hosts_dict[key][k]
    # cmdRun(cmd, ip, port, user, passwd, pkey) 
    c = threading.Thread(target=cmdRun,args=(cmd, ip, port, user, passwd, pkey))
    threads.append(c)
  for t in threads:
    t.setDaemon(True)
    t.start()
  t.join()


def cmdRsync(file_src, file_dest, ip, port, user, passwd, pkey):
  """ 路径解析, rsync命令调用 """
  ssh_key_args = '"ssh -p %s -i %s -q -o StrictHostKeyChecking=no"' % (port, pkey)
  ssh_pwd_args = '"ssh -p %s -q -o StrictHostKeyChecking=no"' % port
  rsync_cmd = '/usr/bin/rsync -a -e'
  start_time = '%s => %s:%s ' %(file_src, ip, file_dest) + strftime("%Y/%m/%d %H:%M:%S -> ",localtime())
  if passwd == 'key':
    subprocess.call('%s %s %s %s@%s:%s' % (rsync_cmd, ssh_key_args, file_src, user, ip, file_dest), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  else:
    pexpect.run('%s %s %s %s@%s:%s' % (rsync_cmd, ssh_pwd_args, file_src, user, ip, file_dest), events={'password': '%s\n' % passwd})
  print start_time + strftime("%H:%M:%S",localtime()) + " ok"

def PathProcess(file_path):
  """ 接收一个路径变量,处理并返回两个有效变量,或报错退出 """ 
  file_num = file_path.split()
  if len(file_num) == 1:
    if not os.path.isabs(file_path):
      print "Error, %s must be an absolute path" % file_path
      sys.exit(3)
    if os.path.isfile(file_path):
      return file_path, file_path
    elif os.path.isdir(file_path):
      if file_path[-1] != '/':
        file_path = '%s/' % file_path
        return file_path, file_path
      else:
        return file_path, file_path
    else:
      print "Error, rsync cannot access %s No such file or directory" % file_path
      sys.exit(3)
  elif len(file_num) == 2:
    if not os.path.isabs(file_num[0]) or not os.path.isabs(file_num[1]):
      print "Error, %s or %s must be an absolute path" % (file_num[0], file_num[1])
      sys.exit(3)
    if os.path.isfile(file_num[0]):
      return file_num
    elif os.path.isdir(file_num[0]):
      if file_num[0][-1] != '/':
        file_num[0] = '%s/' % file_num[0]
      if file_num[1][-1] != '/':
        file_num[1] = '%s/' % file_num[1] 
      return file_num
    else:
      print "Error, rsync cannot access %s No such file or directory" % file_num[0]
      sys.exit(3)
  else:
    print "Error, Invalid path : %s" % file_path


def fileSync(file_path, hosts_dict):
  """ 将传递进来的文件/目录,同步到传递字典的每个ip """ 
  file_src, file_dest = PathProcess(file_path)
  #print "%s %s" % (file_src, file_dest)
  for key in hosts_dict:
    port = 22
    user = getpass.getuser()
    passwd = 'key'
    pkey = os.environ['HOME'] + '/.ssh/id_rsa'
    for k in hosts_dict[key]:
      if k == 'ip':
        ip = hosts_dict[key][k]
      elif k == 'port':
        port = int(hosts_dict[key][k])
      elif k == 'user':
        user = hosts_dict[key][k]
      elif k == 'passwd':
        passwd = hosts_dict[key][k]
      elif k == 'pkey':
        pkey = hosts_dict[key][k]
    cmdRsync(file_src, file_dest, ip, port, user, passwd, pkey)

def functionRouting(opts, args):
  """ 详细区分参数后引用 """
  for k, v in opts:
    if k in ('-c', '--command'):
      cmdRoute(v, hosts_dict)  
    elif k in ('-f', '--file'):
      fileSync(v, hosts_dict)
    elif k in ('-i', '--install'):
      installPackage()
    elif k in ('-h', '--help'):
      usage()
      sys.exit(0)
    else:
      print 'Ivalid params'
      usage()
      sys.exit(3)

def main(argv):
  """ 简单处理参数后,将有效参数扔给 functionRouting 处理 """
  short_args = 'c:f:hi'
  long_args = ['command=', 'file=', 'help', 'install'] 
  try:
    opts, args = getopt.getopt(argv[1:], short_args, long_args)
  except getopt.GetoptError, err:
    print str("Ivalid params")
    usage()
    sys.exit(2)
  functionRouting(opts, args)

if __name__ == '__main__':
  conf = '/etc/hdp.cfg'
  if not os.path.isfile(conf):
    print "%s invalid configuration file" % conf
    sys.exit(1)
  cf = ConfigParser.ConfigParser()
  cf.read(conf)
  hosts_file = cf.get('basic', 'hosts_file')
  hosts_dict = hostsHash(hosts_file)
  main(sys.argv)

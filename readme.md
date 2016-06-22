# hhdp

#### Table of Contents

1. [简介](#简介)
2. [描述](#描述)
3. [安装说明](#安装说明)
4. [使用说明](#使用说明)
  *  [主机列表文件(/etc/hosts_list)格式说明](#主机列表文件(/etc/hhdp_hosts)格式说明)
  *  [命令具体使用](#命令具体使用)
5. [目前问题](#目前问题)

## 简介

####  hhdp是一个用来在多个linux节点上并发执行shell命令和同步文件或目录的一个小工具

## 描述

* 此工具使用python编写
* 使用此工具之前需要手工编写一个主机列表文件

## 安装说明

```
1. 安装依赖包:
  Ubuntu:
    apt-get -y install rsync python-paramiko python-pexpect
  Redhat/CentOS:
    yum -y install rsync python-paramiko python-pexpect
2. 获取代码:
  git clone https://github.com/bw-y/hhdp.git
  chmod 755 hhdp.py && mkdir -v /usr/local/hhdp
  mv hhdp.py /usr/local/hhdp/
3. 创建主机列表文件:/etc/hosts_list
  touch /etc/hosts_list # 文件内容说明见下文
4. 创建链接:
  ln -sv /usr/local/hhdp/hhdp.py /usr/bin/hhdp
```

## 使用说明
  
### 主机列表文件(/etc/hhdp_hosts)格式说明

  * 此文件默认路径: /etc/hhdp_hosts
  * 支持注释,任意行首`#`时,此行内容不被读取
  * 文件每行定义一个主机相关信息(ip,port,user,passwd,pkey),其中pkey为ssh使用key认证时,私钥文件的绝对路径
  * 每行多个字段之间以一个空格隔开,字段内容由冒号定义属性. 例如: `ip:192.168.1.10 port:22 pkey:/opt/id_rsa`
  * 除ip字段外,其它属性都有默认值,可不填写.
  * ip     [必填项]可以是ip和fqdn.    例: `ip:192.168.1.10` 或: `ip:node1.bw-y.com`
  * port   [可选项]调用ssh所需端口号. 例: `port:1022`            默认值: `port:22`
  * user   [可选项]调用ssh所需用户名. 例: `user:bw_y`            默认值: `user:root`
  * passwd [可选项]调用ssh所需密码.   例: `passwd:ssh_password`  默认值: `passwd:key`(使用pkey对应的值,passwd不等于key时,则直接使用密码)
  * pkey   [可选项]调用ssh所需私钥.   例: `pkey:/opt/pro/id_rsa` 默认值: 当前用户家目录下的.ssh目录中的id_rsa, 此文件不存在时直接报错.

#### 例: 一个完成的主机列表文件如下

```
# cat /etc/hhdp_hosts 
ip:192.168.5.22 user:bw-y
ip:192.168.5.12 passwd:redhat
ip:lab.bw-y.com
ip:192.168.5.43 pkey:/opt/id_rsa
ip:node1.bw-y.com port:1002 pkey:/opt/bw_id_rsa
```

### 命令具体使用
  
注: 如果需要执行的命令过长,或者命令中有用到单引号或其它特殊符号,可以先写一个简单的脚本,hhdp -f将其推送到每个节点上,然后hhdp -c调用脚本执行

```
例1. 将命令 `uptime` 在每个节点上执行
# hhdp -c 'uptime'
 23:52:49 up 1 day,  9:43,  0 users,  load average: 0.22, 0.30, 0.33
 23:52:49 up 1 day,  9:49,  2 users,  load average: 0.00, 0.00, 0.00
 23:52:50 up 1 day,  9:48,  0 users,  load average: 0.26, 0.13, 0.08
 23:52:50 up 2 days, 21:40,  3 users,  load average: 0.34, 0.13, 0.08

例2. 将命令 `facter hostname;facter ipaddress;uptime|grep "1 day";echo` 在每个节点上执行
# hhdp -c 'hostname;facter ipaddress;uptime|grep "1 day";echo'
centos6
192.168.5.12
 00:00:25 up 1 day,  9:57,  2 users,  load average: 0.00, 0.01, 0.00

ubt12-04
192.168.5.14
 00:00:25 up 1 day,  9:55,  0 users,  load average: 0.26, 0.18, 0.11

ubt10-04
192.168.5.18
 00:00:25 up 1 day,  9:51,  0 users,  load average: 0.23, 0.28, 0.31

docker
172.17.42.1


例3. 将本地文件/opt/file1同步到每个节点的相同路径
# hhdp -f /opt/file1 
/opt/file1 => 192.168.5.18:/opt/file1 2015/10/07 00:06:17 -> 00:06:20 ok
/opt/file1 => 192.168.5.17:/opt/file1 2015/10/07 00:06:20 -> 00:06:24 ok
/opt/file1 => 192.168.5.16:/opt/file1 2015/10/07 00:06:24 -> 00:06:28 ok
/opt/file1 => 192.168.5.15:/opt/file1 2015/10/07 00:06:28 -> 00:06:31 ok

例4. 将本地文件/opt/file1同步到每个节点的/tmp/file2
# hhdp -f /opt/file1 /tmp/file2
/opt/file1 => 192.168.5.18:/tmp/file2 2015/10/07 00:07:42 -> 00:07:45 ok
/opt/file1 => 192.168.5.17:/tmp/file2 2015/10/07 00:07:45 -> 00:07:50 ok
/opt/file1 => 192.168.5.16:/tmp/file2 2015/10/07 00:07:50 -> 00:07:53 ok
/opt/file1 => 192.168.5.15:/tmp/file2 2015/10/07 00:07:53 -> 00:07:56 ok

例5. 获取刚才推荐文件的md5
# hhdp -c 'echo "$(hostname) $(md5sum /tmp/file2)"'
centos6 b2c08b9857557daeb960752600c0cc91  /tmp/file2
ubt10-04 b2c08b9857557daeb960752600c0cc91  /tmp/file2
ubt12-04 b2c08b9857557daeb960752600c0cc91  /tmp/file2
docker b2c08b9857557daeb960752600c0cc91  /tmp/file2

例6. 将本地目录/opt/dir同步到每个节点的相同位置
# hhdp -f /opt/dir
/opt/dir/ => 192.168.5.18:/opt/dir/ 2015/10/07 00:12:48 -> 00:12:51 ok
/opt/dir/ => 192.168.5.17:/opt/dir/ 2015/10/07 00:12:51 -> 00:12:54 ok
/opt/dir/ => 192.168.5.16:/opt/dir/ 2015/10/07 00:12:54 -> 00:12:57 ok
/opt/dir/ => 192.168.5.15:/opt/dir/ 2015/10/07 00:12:57 -> 00:12:59 ok


例7. 将本地目录/opt/dir同步到每个节点的/tmp/dir目录
# hhdp -f /opt/dir /tmp/dir
/opt/dir/ => 192.168.5.18:/tmp/dir/ 2015/10/07 00:14:08 -> 00:14:11 ok
/opt/dir/ => 192.168.5.17:/tmp/dir/ 2015/10/07 00:14:11 -> 00:14:14 ok
/opt/dir/ => 192.168.5.16:/tmp/dir/ 2015/10/07 00:14:14 -> 00:14:18 ok
/opt/dir/ => 192.168.5.15:/tmp/dir/ 2015/10/07 00:14:18 -> 00:14:21 ok
```

## 目前问题
### 线程数量过多会导致SSH相关异常,目前暂未找到更好的解决方法.

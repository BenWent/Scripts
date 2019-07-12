#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: ben
# @Date:   2019-07-12 09:21:03
# @Last Modified by:   ben
# @Last Modified time: 2019-07-12 14:29:56
# @Description:        distribute the hadoop environment to each machine in clusters

import os
import socket
import paramiko
import getpass

# 删除原有的hadoop包
os.system('rm -f /tmp/hadoop-2.8.5.tar.gz')
# 对配置好的hadoop重新进行进行打包
os.system('tar -zcf  /tmp/hadoop-2.8.5.tar.gz /opt/hadoop-2.8.5')

# 获取本机ip
hostname = socket.gethostname()
m_ip = socket.gethostbyname(hostname)

# 集群中各台机器的root密码
root_password = getpass.getpass('root password: ')
# 待上传文件的位置
local_path = r'/tmp/hadoop-2.8.5.tar.gz'
# 文件的上传位置，需要指定文件上传后的文件名
remote_path = r'/tmp/hadoop-2.8.5.tar.gz'

with open('/etc/hosts', mode='r') as file:
    for line in file:
        ip_name = line.strip().split()
        # print(ip_name)
        if len(ip_name) != 2:
            continue

        ip = ip_name[0]

        if ip == m_ip:
            continue

        # 将配置好的hadoop进行分发
        transport = paramiko.Transport((ip, 22))
        transport.connect(username='root', password=root_password)
        client = paramiko.SFTPClient.from_transport(transport)

        client.put(local_path, remote_path)

        transport.close()

        # 创建ssh对象
        ssh = paramiko.SSHClient()
        # 允许连接不在know_hosts文件中的主机
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # 连接服务器
        ssh.connect(hostname=ip, port=22, username='root',
                    password=root_password)

        # 解压缩
        ssh.exec_command('tar -zxf /opt/hadoop-2.8.5.tar.gz -C /opt')
        ssh.exec_command('mv /opt/opt/hadoop-2.8.5 /opt')
        ssh.exec_command('rm -fr /opt/opt')
        ssh.exec_command('chown -R hadoop /opt/hadoop-2.8.5')

        # 退出ssh连接
        ssh.close()
        break

# 参考：
# 1、Python paramik：https://blog.csdn.net/u012881331/article/details/82881053

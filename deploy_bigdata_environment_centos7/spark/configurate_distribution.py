#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: ben
# @Date:   2019-07-12 21:41:04
# @Last Modified by:   ben
# @Last Modified time: 2019-07-13 15:39:16
# @Description:        deploy the environment of spark based on the environment of hadoop

import os
import socket
import paramiko
import getpass

# 下载spark的安装包
# os.system('wget -P /opt http://mirror.bit.edu.cn/apache/spark/spark-2.4.3/spark-2.4.3-bin-hadoop2.7.tgz')
# 解压
# os.system('tar zxf spark-2.4.3-bin-hadoop2.7.tgz')
# 配置环境变量

# 待上传文件的位置
local_path = r'/tmp/spark-2.4.3-bin-hadoop2.7.tgz'
# 文件的上传位置，需要指定文件上传后的文件名
remote_path = r'/tmp/spark-2.4.3-bin-hadoop2.7.tgz'

# 删除原有的spark包
os.system('rm -f {local_path}'.format(local_path=local_path))
# 对配置好的hadoop重新进行进行打包
os.system(
    'tar -zcf  {local_path} /opt/spark-2.4.3-bin-hadoop2.7'.format(local_path=local_path))

# 获取本机ip
hostname = socket.gethostname()
m_ip = socket.gethostbyname(hostname)

# 集群中各台机器的root密码
root_password = getpass.getpass('root password: ')

with open('/etc/hosts', mode='r') as file:
    for line in file:
        ip_name = line.strip().split()
        # print(ip_name)
        if len(ip_name) != 2:
            continue

        ip = ip_name[0]

        if ip == m_ip:
            continue

        # 创建ssh对象
        ssh = paramiko.SSHClient()
        # 允许连接不在know_hosts文件中的主机
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # 连接服务器
        ssh.connect(hostname=ip, port=22, username='root',
                    password=root_password)

        # 将配置好的spark发送到slave机器
        sftp = ssh.open_sftp()
        sftp.put(local_path, remote_path)

        # 删除原有的配置
        _, stdout, _ = ssh.exec_command('rm -fr /opt/spark-2.4.3-bin-hadoop2.7')
        stdout.channel.recv_exit_status()

        # 解压缩
        stdin, stdout, stderr = ssh.exec_command(
            'tar -zxf {remote_path} -C /tmp'.format(remote_path=remote_path))
        stdout.channel.recv_exit_status()  # 阻塞直到 exec_command 命令执行完毕

        _, stdout, _ = ssh.exec_command(
            'mv /tmp/opt/spark-2.4.3-bin-hadoop2.7 /opt')
        stdout.channel.recv_exit_status()

        _, stdout, _ = ssh.exec_command(
            'chown -R hadoop /opt/spark-2.4.3-bin-hadoop2.7')
        stdout.channel.recv_exit_status()

        # 删除文件
        _, stdout, _ = ssh.exec_command('rm -fr /tmp/opt')
        stdout.channel.recv_exit_status()
        sftp.remove(remote_path)

        # 删除文件
        # sftp.rmdir('/opt/opt') # 使用sftp.rmdir删除目录必须要确保该目录是空的

        # 退出ssh连接
        ssh.close()
        # break

# 参考：
# 1、Spark Standalone Mode：https://spark.apache.org/docs/latest/spark-standalone.html
# 2、basic-paramiko-exec-command-help：https://stackoverflow.com/questions/7002878/basic-paramiko-exec-command-help
# 1）recv_exit_status()解释：
# https://paramiko-docs.readthedocs.io/en/latest/api/channel.html#paramiko.channel.Channel.recv_exit_status

# -*- coding: utf-8 -*-

import os
import commands
import paramiko
import getpass


# 集群中各台机器的root密码
root_password = getpass.getpass('root password: ')

with open('/etc/hosts', mode='r') as file:
    for line in file:
        ip_name = line.strip().split()
        # print(ip_name)
        if len(ip_name) != 2:
            continue

        ip = ip_name[0]

        # 创建ssh对象
        ssh = paramiko.SSHClient()
        # 允许连接不在know_hosts文件中的主机
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # 连接服务器
        ssh.connect(hostname=ip, port=22, username='root',
                    password=root_password)

        ssh.exec_command("echo '\n# 配置Spark环境' >> /etc/profile")
        ssh.exec_command(
            "echo 'export SPARK_HOME=/opt/spark-2.4.3-bin-hadoop2.7' >> /etc/profile")
        ssh.exec_command(
            "echo 'export PATH=$PATH:$SPARK_HOME/bin:$SPARK_HOME/sbin' >> /etc/profile")

        # 使配置的环境生效
        ssh.exec_command('source /etc/profile')

        # 退出ssh连接
        ssh.close()


# 参考
# 1、python调用linux的命令：https://www.cnblogs.com/hujq1029/p/7096247.html
# 2、basic-paramiko-exec-command-help：https://stackoverflow.com/questions/7002878/basic-paramiko-exec-command-help
# 1）recv_exit_status()解释：
# https://paramiko-docs.readthedocs.io/en/latest/api/channel.html#paramiko.channel.Channel.recv_exit_status

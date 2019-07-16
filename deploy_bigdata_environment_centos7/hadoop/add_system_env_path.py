# -*- coding: utf-8 -*-

import os
import commands
import paramiko
import getpass


# 集群中各台机器的root密码
root_password = getpass.getpass('root password: ')

# 取第一个位置作为配置环境变量的位置（可能在多处下载并解压了hadoop）
command_location = commands.getoutput(
    'find / -name hadoop-daemons.sh').split(r'\n')[0]

if len(command_location) <= 0:
    print('you did not download hadoop package or decompose it')
    os._exit(1)

hadoop_location_index = command_location.rfind(
    r'/', 0, command_location.rfind(r'/'))
# hadoop的解压位置
hadoop_location = command_location[:hadoop_location_index]

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

        # 安装open-jdk
        # os.system('yum -y install java-1.7.0-openjdk')
        _, stdout, _ = ssh.exec_command(
            'yum -y install java-1.8.0-openjdk-devel')
        stdout.channel.recv_exit_status()

        java_link_path = commands.getoutput('ls -l /etc/alternatives/java')
        java_home = java_link_path.split('->')[1][:-13]
        java_home = java_home.strip()

        # 配置jdk环境
        ssh.exec_command("echo -e '\n\n\n# 配置jdk环境' >> /etc/profile")
        ssh.exec_command(
            "echo 'export JAVA_HOME=%s' >> /etc/profile" % java_home)
        ssh.exec_command(
            "echo 'export JRE_HOME=$JAVA_HOME/jre' >> /etc/profile")
        ssh.exec_command(
            "echo 'export CLASSPATH=$JAVA_HOME/lib:$JRE_HOME/lib:$CLASSPATH' >> /etc/profile")
        ssh.exec_command(
            "echo 'export PATH=$JAVA_HOME/bin:$JRE_HOME/bin:$PATH' >> /etc/profile")

        # 配置hadoop的环境
        ssh.exec_command("echo -e '\n# 配置hadoop环境' >> /etc/profile")
        ssh.exec_command(
            "echo 'export HADOOP_HOME={hadoop_location}' >> /etc/profile".format(hadoop_location=hadoop_location))
        ssh.exec_command(
            "echo 'export PATH=$HADOOP_HOME/bin:$HADOOP_HOME/sbin:$PATH' >> /etc/profile")

        # 使配置的环境生效
        _, stdout, _ = ssh.exec_command('source /etc/profile')
        stdout.channel.recv_exit_status()

        # 退出ssh连接
        ssh.close()

# 确保安装了wget
# os.system('yum -y install wget')

# 下载并解压hadoop源码到 /opt
# os.system('wget -P /opt http://mirror.bit.edu.cn/apache/hadoop/common/hadoop-2.8.5/hadoop-2.8.5.tar.gz')
# os.system('tar -zxf /opt/hadoop-2.8.5.tar.gz -C /opt/')


# 参考
# 1、python调用linux的命令：https://www.cnblogs.com/hujq1029/p/7096247.html

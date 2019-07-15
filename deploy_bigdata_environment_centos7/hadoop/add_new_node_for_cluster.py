#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: ben
# @Date:   2019-07-13 16:49:33
# @Last Modified by:   ben
# @Last Modified time: 2019-07-15 21:42:04
# @Description:        向hadoop集群中添加新的节点

import os
import commands
import paramiko
import getpass
import random
import crypt
import time
import socket
import configparser


def set_login_without_passward(src_ip, dst_ip, password):
    ''' 设置src_ip到dst_ip的免密码登录 '''

    # 集群各节点到新增节点之间的免密码登录
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=src_ip, port=22, username=user,
                   password=password)

    # 配置SSH互信
    channel = client.invoke_shell()
    channel.send(
        "ssh-copy-id -i ~/.ssh/id_rsa.pub {user}@{ip}\n".format(user=user, ip=dst_ip))
    while not channel.recv_ready():
        time.sleep(0.1)

    # 等待对方发送全部信息
    time.sleep(2)
    resp = channel.recv(9999)
    # 如果出现Are you sure you want to continue connecting (yes/no)?，
    # 将指定的ip的认证添加到  ~/.ssh/known_hosts 文件中
    if resp.find('?') != -1:
        channel.send('yes\n')
        while not channel.recv_ready:
            time.sleep(0.1)

        time.sleep(2)
        resp = channel.recv(9999)
    # print(resp)
    if resp.find('password:') != -1:  # 如果出现了 password:，输入该台机器的密码
        channel.send('%s\n' % password)
        while not channel.recv_ready():  # 确保的密码输入
            time.sleep(0.1)
    time.sleep(1)

    client.close()


if __name__ == '__main__':
    parser = configparser.ConfigParser()
    parser.read('add_new_node_config.ini')

    # 待添加到集群中的新节点ip
    ips = parser.get('section', "ips")
    ip_list = ips.split(',')
    ip_list = list(map(lambda s: s.strip(), ip_list))
    # 待添加到集群中的新节点机器名
    hostnames = parser.get('section', 'hostnames')
    hostname_list = hostnames.split(',')
    hostname_list = list(map(lambda s: s.strip(), hostname_list))
    # 集群中各个节点间的通信用户及其密码
    user = parser.get('section', 'user')
    password = parser.get('section', 'password')  # 新增节点的密码要与集群各个节点的密码一致
    encrypted_password = crypt.crypt(password, str(random.randint(0, 9999)))

    # 集群中root用户的密码不由配置文件指定，而由用户输入
    root_password = getpass.getpass('root password(cluster):')

    # 获取本机ip
    hostname = socket.gethostname()
    m_ip = socket.gethostbyname(hostname)

    hadoop_home = commands.getoutput('echo ${HADOOP_HOME}')

    # 添加路由
    with open('/etc/hosts', mode='r') as file:
        for line in file:
            fragments = line.strip().split()
            if len(fragments) != 2:
                continue

            _ip = fragments[0]
            _hostname = fragments[1]

            # 以root身份ssh登录到其它机器
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(hostname=_ip, username='root',
                           password=root_password)
            for index, ip in enumerate(ip_list):  # 为每台节点的hosts文件中添加新增节点的路由
                name = hostnames[index]

                if m_ip != _ip:  # 运行节点需要单独处理，以防造成无限循环
                    _, stdout, _ = client.exec_command(
                        "echo -e '{machine_ip}\t{machine_name}' >> /etc/hosts".format(machine_name=name, machine_ip=ip))
                    stdout.channel.recv_exit_status()

                # 为每个节点中的hadoop配置中添加该新增节点的hostname
                _, stdout, _ = client.exec_command(
                    "echo '{machine_name}' >> {hadoop_home}/etc/hadoop/slaves".format(machine_name=name, hadoop_home=hadoop_home))
                stdout.channel.recv_exit_status()

            client.close()

            # 将当前集群中的所有机器的ip到hostname的映射写入到一个临时文件中
            os.system("echo -e '{machine_ip}\t{machine_name}' >> ./hosts.tmp".format(
                machine_name=_hostname, machine_ip=_ip))

    for index, ip in enumerate(ip_list):
        name = hostnames[index]

        # 为运行该脚本的节点单独添加新增节点的路由
        os.system("echo -e '{machine_ip}\t {machine_name}' >> /etc/hosts".format(
            machine_name=name, machine_ip=ip))

        # 将当前集群中的所有机器的ip到hostname的映射写入到一个临时文件中
        os.system("echo -e '{machine_ip}\t{machine_name}' >> ./hosts.tmp".format(
            machine_name=name, machine_ip=ip))

        # 登录到新增节点
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=ip, username='root', password=root_password)

        # 获取当前安装的openjdk版本
        java_version = commands.getoutput(
            'java -version').split('\n')[0].split()[-1].split('_')[0].replace('\"', "")

        # 安装open-jdk
        _, stdout, _ = client.exec_command(
            'yum -y install java-{java_version}-openjdk-devel'.format(java_version=java_version))
        stdout.channel.recv_exit_status()

        java_link_path = commands.getoutput('ls -l /etc/alternatives/java')
        java_home = java_link_path.split('->')[1][:-13]
        java_home = java_home.strip()

        # 配置jdk环境
        client.exec_command("echo -e '\n\n\n# 配置jdk环境' >> /etc/profile")
        client.exec_command(
            "echo 'export JAVA_HOME=%s' >> /etc/profile" % java_home)
        client.exec_command(
            "echo 'export JRE_HOME=$JAVA_HOME/jre' >> /etc/profile")
        client.exec_command(
            "echo 'export CLASSPATH=$JAVA_HOME/lib:$JRE_HOME/lib:$CLASSPATH' >> /etc/profile")
        client.exec_command(
            "echo 'export PATH=$JAVA_HOME/bin:$JRE_HOME/bin:$PATH' >> /etc/profile")

        # 获得hadoop名
        hadoop_name = os.path.basename(hadoop_home)
        hadoop_installation = os.path.dirname(hadoop_home)
        hadoop_top_dir = hadoop_home.split('/')[1]
        # 压缩hadoop配置文件
        os.system('tar -zcf /tmp/{hadoop_name}.tgz {hadoop_home}'.format(
            hadoop_home=hadoop_home, hadoop_name=hadoop_name))
        # 分发
        sftp = client.open_sftp()
        sftp.put('/tmp/{hadoop_name}.tgz'.format(hadoop_name=hadoop_name),
                 '/tmp/{hadoop_name}.tgz'.format(hadoop_name=hadoop_name))
        # 解压
        _, stdout, _ = client.exec_command(
            'tar -zxf /tmp/{hadoop_name}.tgz -C /tmp'.format(hadoop_name=hadoop_name))
        stdout.channel.recv_exit_status()
        print(stdout.read())
        # 将hadoop配置文件放到指定位置
        _, stdout, _ = client.exec_command(
            'mv /tmp/{hadoop_home} {hadoop_installation}'.format(hadoop_home=hadoop_home, hadoop_installation=hadoop_installation))
        stdout.channel.recv_exit_status()
        # 更改权限
        _, stdout, _ = client.exec_command(
            'chown -R {user} {hadoop_home}'.format(user=user, hadoop_home=hadoop_home))
        stdout.channel.recv_exit_status()
        # 删除解压文件
        _, stdout, _ = client.exec_command(
            'rm -fr /tmp/{hadoop_top_dir}'.format(hadoop_top_dir=hadoop_top_dir))
        stdout.channel.recv_exit_status()
        # 删除新增节点的临时压缩包
        sftp.remove('/tmp/{hadoop_name}.tgz'.format(hadoop_name=hadoop_name))
        # 删除本地的临时压缩包
        os.system(
            'rm -f /tmp/{hadoop_name}.tgz'.format(hadoop_name=hadoop_name))

        # 配置hadoop的环境
        client.exec_command("echo -e '\n# 配置hadoop环境' >> /etc/profile")
        client.exec_command(
            "echo 'export HADOOP_HOME={hadoop_home}' >> /etc/profile".format(hadoop_home=hadoop_home))
        _, stdout, _ = client.exec_command(
            "echo 'export PATH=$HADOOP_HOME/bin:$HADOOP_HOME/sbin:$PATH' >> /etc/profile")
        stdout.channel.recv_exit_status()

        # 使配置的环境生效
        _, stdout, _ = client.exec_command('source /etc/profile')
        stdout.channel.recv_exit_status()

        # 获得user用户唯一标识符
        _, stdout, _ = client.exec_command('id -u {user}'.format(user=user))
        stdout.channel.recv_exit_status()
        user_id = stdout.readline()
        if not user_id.isdigit():  # user用户不存在，才创建新的用户
            # -r指定创建系统用户，-m指定创建home目录
            _, stdout, _ = client.exec_command(
                'useradd -r -m -s /bin/bash -p {password} {user}'.format(user=user, password=encrypted_password))
            stdout.channel.recv_exit_status()

        # 生成密钥
        try:
            sftp.stat('/home/{user}/.ssh/id_rsa'.format(user=user))
        except IOError:  # user用户没有执行过ssh-keygen命令
            # -f指定将生成的密钥放到哪个文件，-N，指定 password phrase，以format的形式输入''的原因直接输入''，会被linux解析为空串，从而导致命令执行错误
            _, stdout, _ = client.exec_command(
                'su {user} -c "ssh-keygen -t rsa -f ~/.ssh/id_rsa -N {phrase}"\n'.format(user=user, phrase="\'\'"))
            stdout.channel.recv_exit_status()

        # 关闭防火墙
        _, stdout, _ = client.exec_command('systemctl stop firewalld')
        stdout.channel.recv_exit_status()

        # 将 hosts.tmp发送给新增节点，并将其写入到新增节点的/etc/hosts文件中
        sftp.put('./hosts.tmp', '/tmp/hosts.tmp')
        _, stdout, _ = client.exec_command('cat /tmp/hosts.tmp >> /etc/hosts')
        stdout.channel.recv_exit_status()
        # 删除临时文件
        sftp.remove('/tmp/hosts.tmp')
        os.system('rm -f ./hosts.tmp')

        client.close()

    # 新增节点与集群节点间SSH互信
    with open('/etc/hosts', mode='r') as file:
        for line in file:
            ip_name = line.strip().split()

            if len(ip_name) != 2:
                continue

            _ip = ip_name[0]

            for ip in ip_list:
                set_login_without_passward(_ip, ip, password)
                set_login_without_passward(ip, _ip, password)

    for ip in ip_list:
        # 在新节点上启动DatanodeManager进行
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=ip, username='root', password=root_password)

        _, stdout, _ = client.exec_command('yarn-daemon.sh start nodemanager')
        stdout.channel.recv_exit_status()
        _, stdout, _ = client.exec_command('start-balamcer.sh')
        stdout.channel.recv_exit_status()

        client.close()

# 参考：
# 1、动态的添加和删除hadoop集群中的节点：https://blog.csdn.net/qq_38617531/article/details/82973043
# 1）新节点中添加账户(useradd -r -m -s /bin/bash -p encrpted_password)，设置无密码登陆(ssh-copy-id user@ip)
# 2）hadoop_dir/etc/hadoop/slaves添加新节点的路由
# 3）/etc/hosts添加新节点路由
# 4）配置openjdk和hadoop环境

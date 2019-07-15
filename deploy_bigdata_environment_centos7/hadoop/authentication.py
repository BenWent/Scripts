# -*- encoding:utf-8 -*-
# Description:在集群之间配置SSH互信，使集群中的机器可以互相免密码登录

import os
import paramiko
import getpass
import crypt
import random
import time

# 以该用户名作为互信登录的用户名
# user = 'hadoop'
user = input('new user:')  # 注意在linux运行，输入字符串时，需要明确地输入引号。如'ok',而不能是ok
# 以该密码作为互信登录用户的密码
# password = '123456'
password = getpass.getpass('new user password:')
encrypted_password = crypt.crypt(password, str(random.randint(0, 9999)))

# root用户密码
root_password = getpass.getpass('root password:')

# 新建用户并生成密钥，关闭防火墙
with open('/etc/hosts', mode='r') as file:
    for line in file:
        ip_name = line.strip().split()
        # print(ip_name)
        if len(ip_name) != 2:
            continue

        ip = ip_name[0]

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # 以root用户登录（创建新用户，关闭防火墙）
        client.connect(hostname=ip, port=22, username='root',
                       password=root_password)

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
            sftp = client.open_sftp()
            sftp.stat('/home/{user}/.ssh/id_rsa'.format(user=user))
        except IOError:  # user用户没有执行过ssh-keygen命令
            # -f指定将生成的密钥放到哪个文件，-N，指定 password phrase，以format的形式输入''的原因直接输入''，会被linux解析为空串，从而导致命令执行错误
            _, stdout, _ = client.exec_command(
                'su {user} -c "ssh-keygen -t rsa -f ~/.ssh/id_rsa -N {phrase}"\n'.format(user=user, phrase="\'\'"))
            stdout.channel.recv_exit_status()
            # print(stdout.read())

            # _, stdout, _ = client.exec_command(
            #    'su {user} -c "ssh-keygen -t rsa -f ~/.ssh/id_rsa -N ''"\n'.format(user=user))
            # 上面的语句在linux上执行后被解析为： su {user} -c "ssh-keygen -t rsa -f
            # ~/.ssh/id_rsa -N "

        # 关闭防火墙
        _, stdout, _ = client.exec_command('systemctl stop firewalld')
        stdout.channel.recv_exit_status()

        # 关闭ssh连接
        client.close()

# 节点机器间SSH互信
with open('/etc/hosts', mode='r') as file:
    for line in file:
        ip_name = line.strip().split()

        if len(ip_name) != 2:
            continue

        ip = ip_name[0]

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # 以root用户登录
        client.connect(hostname=ip, port=22, username=user,
                       password=password)

        with open('/etc/hosts', mode='r') as _file:
            for _line in _file:
                _ip_name = _line.strip().split()

                if len(_ip_name) != 2:
                    continue

                _ip = _ip_name[0]

                # 配置SSH互信
                channel = client.invoke_shell()
                channel.send(
                    "ssh-copy-id -i ~/.ssh/id_rsa.pub {user}@{ip}\n".format(user=user, ip=_ip))
                while not channel.recv_ready():
                    time.sleep(0.1)

                # 等待对方发送全部信息
                time.sleep(2)
                resp = channel.recv(9999)
                if resp.find('?') != -1:  # 如果出现Are you sure you want to continue connecting (yes/no)?，将指定的ip的认证添加到  ~/.ssh/known_hosts 文件中
                    channel.send('yes\n')
                    while not channel.recv_ready:
                        time.sleep(0.1)

                    time.sleep(2)
                    resp = channel.recv(9999)
                print(resp)
                if resp.find('password:') != -1:  # 如果出现了 password:，输入该台机器的密码
                    channel.send('%s\n' % password)
                    while not channel.recv_ready():  # 确保的密码输入
                        time.sleep(0.1)
                time.sleep(1)

        client.close()


# 参考
# 1、Executing ssh-keygen automatically with Paramiko：
# https://stackoverflow.com/questions/55672657/executing-ssh-keygen-automatically-with-paramiko
# 2、Executing su user (without password) on paramiko ssh
# connection：https://stackoverflow.com/questions/8418026/executing-su-user-without-password-on-paramiko-ssh-connection
# 3、example_paramiko_with_tty.py：https://gist.github.com/rtomaszewski/3397251

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: ben
# @Date:   2019-07-14 18:33:43
# @Last Modified by:   ben
# @Last Modified time: 2019-07-14 18:42:30
# @Description: 	   移除所以集群指定用户以及该用户间的免密码登录

import paramiko
import getpass


# 待移除的用户
user = input('user:')
# root用户密码
root_password = getpass.getpass('root password:')

# 新建用户并生成密钥
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

        _, stdout, _ = client.exec_command(
            'userdel -r {user}'.format(user=user))
        stdout.channel.recv_exit_status()

        # 关闭连接
        client.close()

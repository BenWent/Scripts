#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: ben
# @Date:   2019-07-14 18:33:43
# @Last Modified by:   ben
# @Last Modified time: 2019-07-15 10:04:55
# @Description: 	   移除集群中的指定用户

import paramiko
import getpass

# 待移除的用户
user = input('user:')
# root用户密码
root_password = getpass.getpass('root password:')

with open('/etc/hosts', mode='r') as file:
    for line in file:
        ip_name = line.strip().split()
        # print(ip_name)
        if len(ip_name) != 2:
            continue

        ip = ip_name[0]

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # 以root用户登录
        client.connect(hostname=ip, port=22, username='root',
                       password=root_password)

        _, stdout, _ = client.exec_command(
            'userdel -r {user}'.format(user=user))
        stdout.channel.recv_exit_status()

        # 关闭连接
        client.close()

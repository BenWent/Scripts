#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: ben
# @Date:   2019-07-14 18:33:43
# @Last Modified by:   ben
# @Last Modified time: 2019-07-17 11:18:33
# @Description: 	   移除集群中的指定用户

import paramiko
import getpass
from tqdm import tqdm

# 待移除的用户
user = input('user:')
# root用户密码
root_password = getpass.getpass('root password:')

with open('/etc/hosts', mode='r') as file:
    # 设置进度条
    bar = tqdm(list(file), bar_format='{l_bar}{bar}|{n_fmt}/{total_fmt}')

    for line in bar:
        ip_name = line.strip().split()
        # print(ip_name)
        if len(ip_name) != 2:
            continue

        ip = ip_name[0]

        # 设置进度条提示
        bar.set_description('removing for {ip}'.format(ip=ip))

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

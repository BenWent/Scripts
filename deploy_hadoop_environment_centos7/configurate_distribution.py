#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: ben
# @Date:   2019-07-12 09:21:03
# @Last Modified by:   ben
# @Last Modified time: 2019-07-12 13:43:53
# @Description:        distribute the hadoop environment to each machine in clusters

import os
import socket

# 删除原有的hadoop包
# os.system('rm -f hadoop-2.8.5.tar.gz')
# 对配置好的hadoop重新进行进行打包
os.system('tar -zcf  /tmp/hadoop-2.8.5.tar.gz /opt/hadoop-2.8.5')

# 获取本机ip
hostname = socket.gethostname()
m_ip = socket.gethostbyname(hostname)

with open('/etc/hosts', mode='r') as file:
    for line in file:
        ip_name = line.strip().split()
        # print(ip_name)
        if len(ip_name) != 2:
            continue

        ip = ip_name[0]

        if ip == m_ip:
            continue

        # 安装hadoop
        os.system('scp /tmp/hadoop-2.8.5.tar.gz root@%s:/opt' % ip)
        os.system(
            "ssh root@%s 'tar -zxf /opt/hadoop-2.8.5.tar.gz -C /opt && \
             mv /opt/opt/hadoop-2.8.5 /opt && rm -fr /opt/opt && \
            chown -R hadoop /opt/hadoop-2.8.5'" % ip)

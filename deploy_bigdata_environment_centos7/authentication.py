# -*- encoding:utf-8 -*-
# Description:在集群之间配置SSH互信，使集群中的机器可以互相免密码登录

import os

# 生成密钥
os.system('ssh-keygen -t rsa')
# 关闭防火墙
os.system('systemctl stop firewalld')

with open('/etc/hosts', mode='r') as file:
    for line in file:
        ip_name = line.strip().split()
        # print(ip_name)
        if len(ip_name) != 2:
            continue

        ip = ip_name[0]
        # 配置SSH互信
        os.system("ssh-copy-id -i ~/.ssh/id_rsa.pub hadoop@%s" % ip)

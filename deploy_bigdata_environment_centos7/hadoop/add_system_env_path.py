# -*- coding: utf-8 -*-

import os
import commands

# 安装open-jdk
# os.system('yum -y install java-1.7.0-openjdk')
os.system('yum -y install java-1.8.0-openjdk-devel')
java_link_path = commands.getoutput('ls -l /etc/alternatives/java')
java_home = java_link_path.split('->')[1][:-13]
java_home = java_home.strip()

# 配置jdk环境
os.system("echo '\n\n\n# 配置jdk环境' >> /etc/profile")
os.system("echo -e 'export JAVA_HOME=%s' >> /etc/profile" % java_home)
os.system("echo 'export JRE_HOME=$JAVA_HOME/jre' >> /etc/profile")
os.system(
    "echo 'export CLASSPATH=$JAVA_HOME/lib:$JRE_HOME/lib:$CLASSPATH' >> /etc/profile")
os.system("echo 'export PATH=$JAVA_HOME/bin:$JRE_HOME/bin:$PATH' >> /etc/profile")

# 配置hadoop的环境
os.system("echo -e '\n# 配置hadoop环境' >> /etc/profile")
os.system("echo 'export HADOOP_HOME=/opt/hadoop-2.8.5' >> /etc/profile")
os.system(
    "echo 'export PATH=$HADOOP_HOME/bin:$HADOOP_HOME/sbin:$PATH' >> /etc/profile")

# 使配置的环境生效
os.system('source /etc/profile')

# 确保安装了wget
# os.system('yum -y install wget')

# 下载并解压hadoop源码到 /opt
# os.system('wget -P /opt http://mirror.bit.edu.cn/apache/hadoop/common/hadoop-2.8.5/hadoop-2.8.5.tar.gz')
# os.system('tar -zxf /opt/hadoop-2.8.5.tar.gz -C /opt/')

# 参考
# 1、python调用linux的命令：https://www.cnblogs.com/hujq1029/p/7096247.html

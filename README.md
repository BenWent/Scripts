# Scripts
some useful scripts

## deploy_bigdata_environment_centos7 

### hadoop

1. prerequisites:
   1. pip install paramiko：Paramiko is a Python (2.7, 3.4+) implementation of the SSHv2 protocol [[1\]](http://www.paramiko.org/#id2), providing both client and server functionality.While it leverages a Python C extension for low level cryptography ([Cryptography](https://cryptography.io/)), Paramiko itself is a pure Python interface around SSH networking concepts.
   2. pip install configparser：used to parse the configuration file *add_new_node_config.ini*
3. pip install tqdm: set progress
   
2. documents
   1. to use these scripts, you need to do following preparations:
      1. download the archive file *hadoop-version*  and decompose it
      2. configure what you want to configure，maybe you have to pay attention to the following files:
         - *hadoop-version*/etc/hadoop/hadoop-env.sh
           - export *JAVA_HOME*=java_location
         - *hadoop-version*/etc/hadoop/core-site.xml
         - *hadoop-version*/etc/hadoop/hdfs-site.xml
         - *hadoop-version*/etc/hadoop/slaves
      3. add all ip-hostname mappings in the cluster to the file */etc/hosts*
   2. run **add_system_env_path.py**: this script will do the followings:
      1. install *java-1.8.0-openjdk-devel* and add it's related environment variables JAVA_HOME, JRE_HOME, CLASSPATH and PATH to the file */etc/profile*;
      2. find hadoop's location you have just configurated and use it as the value of a environment variable HADOOP_HOME and also add hadoop-related environment variable PATH in the file */etc/profile* .
   3. run **authentication.py**
      1. you must provide following information:
         1. input a *user name* which you will  use it as the user in linux to manage the whole cluster;
         2. input a *password* which will be used to the password of the provided user;
         3. input *root password* to login into the linux cluster.
      2. this script will do the followings:
         1. use the *user name* you provided to **create a user** in every machine in cluster;
         2. execute  ***ssh-keygen*** command to produce key-pair in each machine of cluster;
         3. execute **ssh-copy-id** command for leting any two machines in the cluster log on to the other machine without password;
         4. copy all the **ip-host mappings** concerned about machine in the cluster in the file **/etc/hosts** on the running machine to the other machines in the cluster;
         5. shutdown the firewall.
   4. run **configurate_distribution.py**
      1. you should provide *root password*;
      2. this script will copy the hadoop you have configured on running machine to the other machines in cluster.
   5. run **add_new_node_for_cluster.py**
      1. you must complete the configuration file **add_new_node_config.ini**
         1. **ip**s: these IPs indicate which machines you want to add to the cluster
         2. **hostname**s: the machines' name corresponding ips
         3. **user**: the user who manage the whole cluster
         4. **password**: the login password of the user you specified
      2. this script will do the followings:
         1. add ip-host mappings from the configuration file to */etc/hosts* of each machine in cluster;
         2. add **hostname** file to *hadoop_version*/etc/hadoop/slaves in every machine in cluster;
         3. install *openjdk*  and add it's related to the file */etc/profile* for machines configured in the configuration file;
         4. add hadoop-related environment variables to the file */etc/profile* for machines configured in the configuration file;
         5. distribute modified hadoop package to each machine configured in the configuration file;
         6. create new user  for machines configurated in the configuration file to manage the cluster;
         7. let any two machines in the cluster log on to the other machine without password;
         8. shutdown the firewall in these machines configurated in the configuration file;
         9. execute hadoop command **yarn-daemon.sh start nodemanager** and **start-balamcer.sh** to create new datanode thread in machines configurated in the configurate file.






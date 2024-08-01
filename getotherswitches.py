from pythonping import ping
import socket
import os
import subprocess
import paramiko
import portal3 

api = portal3.PortalAPI(api_user="netops-api", api_key="2127c497de605b24253cfc7ffd02f5524f85cf33")

otherswitches = []

for each in api.netdb_devices():
    try:
        if each['status'] == 1 and each['product']['vendor']['name'] == 'Arista' and (each['name'].endswith('-ma1') or each['name'].endswith('-ma2') or each['name'].endswith('-t1') or each['name'].endswith('-t2')):
            switch = each['name'] + '.' + each['site']['dns_prefix']
            otherswitches.append(switch)
    except TypeError:
        pass
ips = []
for each in otherswitches:
    try:
        result= socket.gethostbyname(each)
        ips.append(result)
    except socket.gaierror:
        pass


switches = []
sites = []
res=[]
for each in ips:
    #print(each)
    try:
        result1= socket.gethostbyaddr(each)
        #print(result1,each)
        switch = (result1[0].split(".tower")[0])
        #print(switch)
        site = switch.split('.')[1]
        switch_pre = switch.split('.')[0]
        switches.append(switch_pre)
        sites.append(site)
        if not os.path.isdir(os.path.join("/apps/nttech/sbharmar/portal-clab-test/lib/snapshot/configs/all_configs/% s" % site)):
            os.mkdir("/apps/nttech/sbharmar/portal-clab-test/lib/snapshot/configs/all_configs/% s" % site)
    except socket.gaierror:
        pass
    except socket.herror:
        pass

host ='10.30.20.21'
port = '22'
username= ''
password = ''

for each in ips:
    try:
        result1= socket.gethostbyaddr(each)
        #print(each,result1)
        switch = (result1[0].split(".tower")[0])
        #print(switch)
        switch_pre = switch.split('.')[0]
        site = switch.split('.')[1]
        remote_path = '/tftpboot/git/% s/' % site
        #print(site)
    # You could add the local_path to the function to define individual places for the
    # files that you download.
        local_path = '/apps/nttech/sbharmar/portal-clab-test/lib/snapshot/configs/all_configs/% s/' % site
        ssh_con = paramiko.SSHClient()
        ssh_con.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_con.connect(host, port, username, password)
        sftp_con = ssh_con.open_sftp()

        all_files_in_path = sftp_con.listdir(path=remote_path)
        #print(all_files_in_path)
        for file in all_files_in_path:
            if file.startswith(switch_pre):
                file_remote = remote_path + file
                file_local = local_path + file

                #print(file_remote) + '>>>' + file_local

                sftp_con.get(file_remote, file_local)
                #sftp_con.put(file_local, file_remote)

        sftp_con.close()
        ssh_con.close()
    except socket.gaierror:
        pass
    except socket.herror:
        pass
#switches = ['7260cx3-r1-1', '7260cx3-r1-2']
#sites = ['ny4', 'ny5']


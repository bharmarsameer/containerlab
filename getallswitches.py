from pythonping import ping
import socket
import os
import subprocess
import paramiko
import portal3 

x = portal3.PortalAPI(api_user="netops-api", api_key="")

coreswitches = []
for each in x.sitedb_production_sites({'type__in': '1,2,3,5'}):
    try:
        if each['dns_prefix'].startswith('aws') or each['dns_prefix'].startswith('WWW') or each['dns_prefix'].startswith('wow') or each['dns_prefix'].startswith('lab') or each['dns_prefix'].endswith('si') or each['dns_prefix'].endswith('ali-cnhk'):
            pass
        elif each['dns_prefix'].startswith('newark'):
            try:
                result0 = ping('core1.' + each['dns_prefix'], count=1)
                result1 = ping('core2.' + each['dns_prefix'], count=1)
                result2 = ping('core3.' + each['dns_prefix'], count=1)
                result3 = ping('core4.' + each['dns_prefix'], count=1)
                if result0.success():
                    coreswitches.append('core1.' + each['dns_prefix'])
                else:
                    pass
                if result1.success():
                    coreswitches.append('core2.' + each['dns_prefix'])
                else:
                    pass
                if result2.success():
                    coreswitches.append('core3.' + each['dns_prefix'])
                else:
                    pass
                if result3.success():
                    coreswitches.append('core4.' + each['dns_prefix'])
                else:
                    pass
            except socket.error:
                pass
        elif each['dns_prefix'].startswith('dc11'):
            try:
                result0 = ping('core1.' + each['dns_prefix'], count=1)
                if result0.success():
                    coreswitches.append('core1.' + each['dns_prefix'])
                else:
                    pass
            except socket.error:
                pass
        else:
            try:
                #print(each['dns_prefix'])
                result1 = ping('core1.' + each['dns_prefix'], count=1)
                result2 = ping('core2.' + each['dns_prefix'], count=1)
                if result1.success():
                    coreswitches.append('core1.' + each['dns_prefix'])
                else:
                    pass
                if result2.success():
                    coreswitches.append('core2.' + each['dns_prefix'])
                else:
                    pass
            except socket.error:
                pass
    except RuntimeError:
        pass

ips = []
for each in coreswitches:
    try:
        result= socket.gethostbyname(each)
        ips.append(result)
    except socket.gaierror:
        pass

switches = []
sites = []
res=[]
for each in ips:
    try:
        result1= socket.gethostbyaddr(each)
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

host ='x.x.x.x'
port = '22'
username= ''
password = ''

for each in ips:
    try:
        result1= socket.gethostbyaddr(each)
        switch = (result1[0].split(".tower")[0])
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

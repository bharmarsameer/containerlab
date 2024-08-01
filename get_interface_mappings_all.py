from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings
disable_warnings(InsecureRequestWarning)
import yaml
import json
import jinja2
import os
from jinja2 import Template
import pandas as pd
from pybatfish.client.session import Session
from pybatfish.datamodel import *
from pybatfish.datamodel.answer import *
from pybatfish.datamodel.flow import *
import portal3
from settings import *
import json,requests
from pythonping import ping
import socket
import os
import subprocess
import paramiko
import pyeapi
import requests

def getJSONapi(uri):
	r = requests.get(uri)
	output = r.content
	d = json.loads(output)
	return d

def create_dict(file1, file2):
    line1 = []
    line2 = []
    with open(file1, "r") as f1:
        lines1 = f1.readlines()
        for each in lines1:
            line1.append(each.rstrip('\n'))
    with open(file2, "r") as f2:
        lines2 = f2.readlines()
        for each in lines2:
            line2.append(each.rstrip('\n'))
    dictionary = dict(zip(line1,line2))
    return dictionary

def main():
    switches = []
    switches2 = [] 
    TID = []
    api = portal3.PortalAPI(api_user=PORTAL_API_USER, api_key=PORTAL_API_KEY)
    for each in api.circuitdb_circuits():
        if (each['circuit_type'] == 'TELCO' or each['circuit_type'] == 'INTRA_DC') and each['status'] == 'production':
            TID.append(each['tid'])
    for each_tid in TID:
        uri = "https://portal.tower-research.com/portal/api/v1/netdb/tid/?username=netops-api&api_key=2127c497de605b24253cfc7ffd02f5524f85cf33&alias__contains=TID%s&is_active=true&device__status=1" % (each_tid)
        apioutput = getJSONapi(uri)
        #print(apioutput)
        count = 0
        count1 = apioutput['meta']['total_count']
        while count <= count1 -1:
            first_switch_hostname = apioutput['objects'][count]['device']['name'] + "." + apioutput['objects'][count]['device']['site']['dns_prefix']
            first_switch_interface = apioutput['objects'][count]['descr']
            if  "Vlan" in first_switch_interface or "meta" in first_switch_hostname or "3850" in first_switch_hostname or "Port-Channel" in first_switch_interface or "3064" in first_switch_hostname or "tap" in first_switch_hostname or "off" in first_switch_hostname:
                pass
            else:
                switches2.append({each_tid:{first_switch_hostname:first_switch_interface}})
            count+=1
    final_dict = {}
    #test start
    coreswitches = []
    switches3 = []
    for each in api.sitedb_production_sites({'type__in': '1,2,3,5'}):
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
            else:
                try:
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
            #print(each)
            result= socket.gethostbyname(each)
            ips.append(result)
        except socket.gaierror:
            pass

    for each in ips:
        try:
            result1= socket.gethostbyaddr(each)
            switch = (result1[0].split(".tower")[0])
            switches3.append(switch)
        except socket.gaierror:
            pass
        except socket.herror:
            pass

    #switches = ['7060sx2-r1-1.alc-gs', '7060sx2-r1-2.alc-gs' ]
    for each_switch in switches3:
        try:
            eapi_param = pyeapi.client.connect(
            transport='https',
            host=each_switch,
            username='',
            password='',
            port=443,)
            eapi_param.transport._context.set_ciphers('DHE-RSA-AES256-SHA')
            c = pyeapi.client.Node( eapi_param )
            lldp_info = c.run_commands(['show lldp neighbors',])
            for each in lldp_info:
                list1 = (each['lldpNeighbors'])
                for each1 in list1:
                    #print(each)
                    if 'eth1' in each1['neighborPort'] or 'eth2' in each1['neighborPort'] or 'eth0' in each1['neighborPort'] or 'eth3' in each1['neighborPort']:
                        pass
                    elif 't1' in each1['neighborDevice'] or 't2' in each1['neighborDevice'] or 'ma1' in each1['neighborDevice'] or 'ma2' in each1['neighborDevice']:
                        site1 = each_switch.split('.')[1]
                        if site1 in each1['neighborDevice'].split('.tower')[0]:
                            switches.append({each_switch:each1['port']})
                            switches.append({each1['neighborDevice'].split('.tower')[0]:each1['neighborPort']})
                            #print({each1['neighborDevice'].split('.tower')[0]:each1['neighborPort']})
        except pyeapi.eapilib.ConnectionError:
            pass
        except TimeoutError:
            pass
        except SSLError:
            pass
        except socket.herror:
            pass
        except socket.gaierror:
            pass
    #print(switches2)
    for each in switches2:
        for k,v in each.items():
            final_dict.setdefault(k, {}).update(v)
    #print(final_dict)
    for i,j in final_dict.items():
        if len(j) == 2:
            for x,y in j.items():
                switches.append({x:y})
    bf = Session(host="localhost")
    bf.set_network('example_dc')
    SNAPSHOT_DIR = './snapshot'
    bf.init_snapshot(SNAPSHOT_DIR, name='snapshot', overwrite=True)
    result = bf.q.layer3Edges().answer().frame()
    devices = []
    loc_switch = []
    remote_switch = []
    loc_interface = []
    loc_site = []
    rem_site = []
    interfaces = []
    local_int_pair = []
    remote_int_pair = []
    visited_connections = set()
    count = 0
    count1 = result.count().Interface
    local_switches = []
    remote_switches = []
    #get local and remote interfaces using batfish
    while (count < count1 - 1):
        interface = result.iloc[count].Interface.interface
        remote_int = result.iloc[count].Remote_Interface.interface
        hostname = result.iloc[count].Interface.hostname
        remote_hostname = result.iloc[count].Remote_Interface.hostname
        site = hostname.split('.')[1]
        remote_site = remote_hostname.split('.')[1]
        count = count + 1
        if interface.startswith("Vlan800") and remote_int.startswith("Vlan800"):
            loc_switch.append(hostname)
            remote_switch.append(remote_hostname)
            loc_site.append(site)
            rem_site.append(remote_site)
            remote_int_pair.append(remote_hostname+remote_int)
            if hostname + interface in visited_connections:
                continue
            switches.append({hostname:interface.replace('Vlan800', 'Ethernet72')})
            switches.append({remote_hostname:remote_int.replace('Vlan800', 'Ethernet72')})
            visited_connections.add(hostname + interface)
            visited_connections.add(remote_hostname + remote_int)
    #print(switches)
    for each_switch_interface in switches:
        #print(each_switch_interface)
        for switch,interface in each_switch_interface.items():
            with open("{}.txt".format(switch), "a") as f:
                f.write(json.dumps(interface) + "\n")
    for each_file in os.listdir('.'):
        if each_file.endswith('.txt') and each_file != "int.txt":
            file2 = each_file
            file1 = "int.txt"
            dictionary = create_dict(file1,file2)
            res = {"ManagementIntf": {
                    "eth0": "Management1"
						},
					"EthernetIntf":
            {key:val.replace('"', '') for key, val in dictionary.items()}}
        with open("{}.json".format(file2), "w") as f:
            f.write(json.dumps(res))
if __name__ == '__main__':
        main()

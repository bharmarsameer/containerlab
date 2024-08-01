import pyeapi
import pprint
from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings
disable_warnings(InsecureRequestWarning)
import yaml
import jinja2
from jinja2 import Template
import portal3
from settings import *
import json
import requests
from pythonping import ping
import pandas as pd
from pybatfish.client.session import Session
from pybatfish.datamodel import *
from pybatfish.datamodel.answer import *
from pybatfish.datamodel.flow import *
from re import findall
from subprocess import Popen, PIPE
import socket
import os
import subprocess
import paramiko

def getJSONapi(uri):
	r = requests.get(uri)
	output = r.content
	d = json.loads(output)
	return d


def main():
    host ='10.30.20.21'
    port = '22'
    username= ''
    password = ''
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
    switches = []
    interfaces = []
    local_int_pair = []
    remote_int_pair = []
    visited_connections = set()
    local_switches = []
    remote_switches = []
    count = 0
    count1 = result.count().Interface
    while (count < count1 - 1):
        interface = result.iloc[count].Interface.interface
        remote_int = result.iloc[count].Remote_Interface.interface
        hostname = result.iloc[count].Interface.hostname
        remote_hostname = result.iloc[count].Remote_Interface.hostname
        site = hostname.split('.')[1]
        remote_site = remote_hostname.split('.')[1]
        count = count + 1
        if (interface.startswith("Vlan800") or interface.endswith("Vlan800")):
            #print(hostname)
            try:
                if ping(hostname, count=1):
                    switch_git = hostname.split('.')[0]
                    site = hostname.split('.')[1]
                    switches.append({'switch_name' : hostname, 'site': site, 'switch': switch_git})
            except RuntimeError:
                pass
        try:
            if interface.startswith("Vlan800") and remote_int.startswith("Vlan800") and ping(hostname, count=1) and ping (remote_hostname, count=1):
                loc_switch.append(hostname)
                remote_switch.append(remote_hostname)
                loc_site.append(site)
                rem_site.append(remote_site)
                remote_int_pair.append(remote_hostname+remote_int)
                if hostname + interface in visited_connections:
                    continue
                devices.append({hostname:interface.replace('Vlan800', 'Ethernet72'),remote_hostname:remote_int.replace('Vlan800', 'Ethernet72')})
                local_switches.append({hostname:interface.replace('Vlan800', 'Ethernet72')})
                remote_switches.append({remote_hostname:remote_int.replace('Vlan800', 'Ethernet72')})
                visited_connections.add(hostname + interface)
                visited_connections.add(remote_hostname + remote_int)
        except RuntimeError:
            pass
    TID = []
    switches = []
    switches1 = []
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
            site = apioutput['objects'][count]['device']['site']['dns_prefix']
            switch = apioutput['objects'][count]['device']['name']
            first_switch_hostname = apioutput['objects'][count]['device']['name'] + "." + apioutput['objects'][count]['device']['site']['dns_prefix']
            first_switch_interface = apioutput['objects'][count]['descr']
            if  "7010" in first_switch_hostname or "Vlan" in first_switch_interface or "meta" in first_switch_hostname or "3850" in first_switch_hostname or "Port-Channel" in first_switch_interface or "3064" in first_switch_hostname or "tap" in first_switch_hostname or "off" in first_switch_hostname:
                pass
            else:
                switches1.append({each_tid:{first_switch_hostname:first_switch_interface}})
            count+=1
    final_dict = {}
    for each in switches1:
        for k, v in each.items():
            final_dict.setdefault(k, {}).update(v)
    for i,j in final_dict.items():
        if len(j) == 2:
            devices.append(j)
    #print(devices)
    switches2 = []
    coreswitches = []
    for each in api.sitedb_production_sites({'type__in': '1,2,3,5'}):
        try:
            if each['dns_prefix'].startswith('aws') or each['dns_prefix'].startswith('WWW') or each['dns_prefix'].startswith('wow') or each['dns_prefix'].startswith('lab') or each['dns_prefix'].endswith('si') or each['dns_prefix'].endswith('ali-cnhk'):
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
    #print(coreswitches)

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
            switches2.append(switch)
        except socket.gaierror:
            pass
        except socket.herror:
            pass

    #switches = ['7060sx2-r1-1.alc-gs', '7060sx2-r1-2.alc-gs' ]
    for each_switch in switches2:
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
                            devices.append({each_switch:each1['port'],each1['neighborDevice'].split('.tower')[0]:each1['neighborPort']})
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
    
    for each in devices:
        print(each)

    for each in devices:
        for i,j in each.items():
            sw = i
            site1 = i.split('.')[1]
            swname = i.split('.')[0]
            switches.append({'switch_name':sw, 'site':site1, 'switch':swname})
    final_int = []
    alldicts = []
    path_to_json = './'
    json_files = [pos_json for pos_json in os.listdir(path_to_json) if pos_json.endswith('.json')]
    for file in json_files:
        with open(file, "r") as f:
            dict = json.load(f)
            alldicts.append({file.split('.txt')[0]:dict['EthernetIntf']})

    tmp = {}
    for d in alldicts:
        #print(d)
        for k, v in d.items():
            for kk, ii in v.items():
                tmp.setdefault(k, {})[ii] = kk
    out = [{k: tmp.get(k, {}).get(v) for k, v in d.items()} for d in devices]
    for each in out:
        print(each)
    dictlist = []
    temp = []
    for each in out:
        print(each)
        for key, value in each.items():
            temp = [key + ":" + value]
            dictlist.append(temp)
    newdict = []
    n = 0
    while n < len(dictlist):
        newdict.append(dictlist[n] + dictlist[n+1])
        n = n + 2

    names = set()
    res = []
    #print(switches)
    for d in switches:
        if not d['switch_name'] in names:
            names.add(d['switch_name'])
            names.add(d['site'])
            res.append(d)
    #for each in newdict:
    #    print(each)
    switchgit = []
    for each in res:
        switchgit.append(each['switch_name'])
    template_file = "eos-test-sb.clab.j2"
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(searchpath="."))
    template = env.get_template(template_file)
    result = template.render(res=res, newdict=newdict)
    with open ('eos-test-sb.clab.yml', 'w') as f:
        f.write(result)
if __name__ == '__main__':
        main()

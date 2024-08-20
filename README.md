# containerlab

Steps to build the lab:

1. Get all switch configs using getallswitches.py and getotherswitches.py. getallswitches gets all the core switches from the environment and getotherswitches gets the other L2 switches which are not cores but has the L3 ciruits terminated on them
2. Containerlab uses docker containers which has its own interface naming convention. e.g. eth1,2... But we still need to map these interfaces to pur production L3 interfaces in order to boot the container with those specific interfaces. We are using our inbuilt NSOT which is portal in our case to get all the L3 interfaces from our production infrastructure. Once we get these interfaces we will map these to the docker container interfaces per switch/container. I am using a flatfile called int.txt to just name the docker interfaces and then i just use this to map the L3 interfaces. So get_interface_mappings_all.py will create a json file per switch container which will contain the mapping of the docker interface to the production L3 interface. e.g.
   _ _cat ~/portal-clab-test/lib/7260cx3-r1-1.ny5.txt.json
{"ManagementIntf": {"eth0": "Management1"}, "EthernetIntf": {"eth1": "Ethernet48/1", "eth2": "Ethernet15/1", "eth3": "Ethernet52/1", "eth4": "Ethernet72"}}_
there are multiple ways to get the L3 interfaces. Another way if your environment doesn't provide with nsot is using batfish tool.
3. Next step is to create a yaml file to build a blueprint of the containerlab toppology. the getyanlgetall.py creates this using eos-test-sb.clab.j2 jinja file which gets the json files created in step2 and also gets the switch configs from the step1 and builds the yaml file. This yaml file tells containerlab to boot the switch container with the interface mapping and the switch configurations.
4. Once we get the yaml file, in order to build the virtual lab, we can use below command to bring the lab up.
_containerlab deploy -t eos-test-sb.clab.yml_

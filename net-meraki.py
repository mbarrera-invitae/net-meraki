#!/usr/bin/env python3
#
# This script fetch network information from Meraki Dashboard
# creds.json can be taken from 'Networking' folder in 1Password
#

SECRET_FILE = '.creds.cfg'
url = "https://api.meraki.com/api/v1/organizations"
payload = None

import os.path
from os import path 
import json
from pprint import pprint
import configparser
import meraki
import requests

def get_meraki_api( ):
    meraki_config = configparser.ConfigParser()
    meraki_config.read(".creds.cfg")
    meraki_config_api = meraki_config['meraki']['api_key']
    return str(meraki_config_api)


def get_headers():
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Cisco-Meraki-API-Key": get_meraki_api()
    }
    return headers

def get_org_info() -> dict:
    try:
        with open(SECRET_FILE) as f:
            headers = get_headers()
            org_info = {}
            response = requests.request('GET', url, headers=headers, data = payload)
            if response.status_code == 200:
                org_data = response.json()
                for i in org_data:
                    org_info['org_id'] = i['id']
                    org_info['org_name'] = i['name']
    except IOError:
        print("File not accessible")    
    return org_info

def get_networks( org_info : dict ) -> dict:
    org_nets = {}
    headers = get_headers()
    url = 'https://api.meraki.com/api/v1/organizations/'+ org_info['org_id']+'/networks'
    response = requests.request('GET', url, headers=headers, data = payload)
    if response.status_code == 200:
        net_info = response.json()
        for i in net_info:
            org_nets[i['name']] = i['id']
    return org_nets

def get_aps( org_info : dict , network_id : str) -> dict :
    headers = get_headers()
    url = 'https://api-mp.meraki.com/api/v1/networks/'+network_id+'/devices'
    response = requests.request('GET', url, headers=headers, data = payload)
    ap_list =[]
    ap_local = {}
    if response.status_code == 200:
        ap_info = response.json()
        for i in ap_info:
            ap_local['serial'] = i['serial']
            ap_local['mac'] = i['mac']
            ap_local['lanIp'] = i['lanIp']
            ap_local['model'] = i['model']
            ap_list.append(ap_local)
            ap_local = {}        
        numberDevices = len(ap_list)
        org_info[network_id]['NumberOfDevices']= str(numberDevices)        
        org_info[network_id]['Devices']= ap_list
    return org_info

def get_properties() -> dict:
    org_properties = get_org_info()
    org_properties['network_ids'] = get_networks(org_properties)
    for site_id in org_properties['network_ids']:
        org_properties[org_properties['network_ids'][site_id]]= {
            'name' : site_id
        }
    for networks in org_properties:
        get_aps(org_properties,networks)
    return org_properties

def main():
    data = get_properties()
    with open('./properties/properties.json','w') as pro:
        json.dump(data,pro, indent=4 )
if __name__== "__main__":
    main()


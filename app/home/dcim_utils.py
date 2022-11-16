import json
import requests


class Instance:
    def __init__(self, dcim_api, token):
        self.dcim_api = dcim_api
        self.dcim_headers = {'Authorization': 'Token ' + token}

    def get_instance_by_ip(self, ip_address):
        params = {'ip_address': ip_address}
        try:
            instance = requests.get(
                self.dcim_api + "instances/", headers=self.dcim_headers,
                params=params).json()['results']
            if not instance:
                return None
            for i in instance:
                instance_address = i['primary_ip4']['address']
                if "/" in instance_address:
                    instance_ip = instance_address.split("/")[0]
                else:
                    instance_ip = instance_address
                if instance_ip == ip_address:
                    instance_id = i['id']
                    return instance_id
            return None
        except:
            return None

    def get_host_info(self, ip_address):
        instance_id = self.get_instance_by_ip(ip_address)
        if not instance_id:
            return None
        try:
            instance_extra_data = requests.get(
                self.dcim_api + "instance-extra-data/?instance_id={}".format(
                    instance_id), headers=self.dcim_headers).json()
            result = {}
            for i in instance_extra_data.get('results'):
                if i.get('instance') == instance_id:
                    port_name = []
                    node_name = []
                    hba = i['metadata_info']['HBA']['rows']
                    for h in hba:
                        port_name.append(
                            h['port_name'].replace("0x", "").strip())
                        node_name.append(
                            h['node_name'].replace("0x", "").strip())
                    hostname = i['metadata_info']['GENERAL']['rows'][0][
                        'hostname']
                    result.update({'port_name': port_name,
                                   'node_name': node_name,
                                   'hostname': hostname})
                    break
            format_json = {
                'wwpns': [
                    '{}'.format(result['port_name'][0]),
                    '{}'.format(result['port_name'][1])
                ],
                'wwnns': [
                    '{}'.format(result['node_name'][0]),
                    '{}'.format(result['node_name'][1])
                ],
                'ip': 'fake',
                'system uuid': 'fake',
                'host': '{}'.format(result['hostname']),
                'mountpoint': '{}'.format(ip_address),
                'multipath': True,
                'initiator': 'iqn.1994-05.com.redhat:fake',
                'platform': 'x86_64',
                'do_local_attach': False,
                'os_type': 'linux2'
            }
            return format_json
        except:
            return None

    def get_host_hostname(self, ip_address):
        instance_id = self.get_instance_by_ip(ip_address)
        if not instance_id:
            return None
        try:
            instance_extra_data = requests.get(
                self.dcim_api + "instance-extra-data/?instance_id={}".format(
                    instance_id), headers=self.dcim_headers).json()
            hostname = ''
            for i in instance_extra_data.get('results'):
                if i.get('instance') == instance_id:
                    hostname = i['metadata_info']['GENERAL']['rows'][0][
                        'hostname']
                    break
            return hostname
        except:
            return None

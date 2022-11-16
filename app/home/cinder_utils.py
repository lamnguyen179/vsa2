import json
import requests

from keystoneauth1.identity import v3
from keystoneauth1 import session


class Volume:
    def __init__(self, api_ip, cinder_port, keystone_port, project, user, pw):
        self.keystone_url = 'http://{}:{}/v3/'.format(api_ip, keystone_port)
        self.cinder_url = 'http://{}:{}/v3/'.format(api_ip, cinder_port)
        self.ops_user = user
        self.ops_pw = pw
        self.ops_pj = project
        self.admin_token = self.get_token(project)
        self.admin_headers = self.set_header(self.admin_token)
        self.project_id = self.get_project_id(project)

    def get_token(self, project_name):
        auth = v3.Password(auth_url=self.keystone_url,
                           user_domain_name='default',
                           username=self.ops_user,
                           password=self.ops_pw,
                           project_domain_name='default',
                           project_name=project_name)
        new_session = session.Session(auth=auth)
        token = new_session.get_token()
        return token

    def set_header(self, token=None):
        if not token:
            token = self.get_token(self.ops_pj)
        return {
            'X-Auth-Token': token,
            'Content-Type': 'application/json',
            'OpenStack-API-Version': 'volume 3.44'
        }

    def get_project_id(self, project_name):
        url = self.keystone_url + 'projects'
        project_list = requests.get(url, headers=self.admin_headers).json()[
            'projects']
        for pj in project_list:
            if pj['name'] == project_name:
                return pj['id']
        return False

    def get_volumes_of_project(self):
        self.admin_headers = self.set_header()
        volume_url = self.cinder_url + self.project_id + '/volumes/detail'
        result = requests.get(volume_url, headers=self.admin_headers)
        volumes = result.json().get('volumes')
        volume_type_url = self.cinder_url + self.project_id + '/types'
        result = requests.get(volume_type_url, headers=self.admin_headers)
        volume_types = result.json().get('volume_types')
        return volumes, volume_types

    def get_volumes_by_id(self, volume_id):
        url = self.cinder_url + self.project_id + '/volumes/' + volume_id
        result = requests.get(url, headers=self.admin_headers)
        volume = result.json().get('volume')
        return volume

    def get_all_volume_type(self):
        url = self.cinder_url + self.project_id + '/types'
        result = requests.get(url, headers=self.admin_headers)
        volume_types = result.json().get('volume_types')
        return volume_types

    def delete_volume(self, volume_id):
        url = self.cinder_url + self.project_id + '/volumes/' + volume_id
        result = requests.delete(url, headers=self.admin_headers)
        return result

    def create_volume(self, size, name, volume_type):
        url = self.cinder_url + self.project_id + '/volumes'
        data = json.dumps({
            "volume": {
                "size": int(size),
                "name": name,
                "volume_type": volume_type,
            }
        })
        result = requests.post(url, headers=self.admin_headers, data=data)
        return result

    def create_attachment(self, host_info, volume_id):
        url = self.cinder_url + self.project_id + '/attachments'
        if not host_info:
            data = None
        else:
            data = json.dumps({
                "attachment": {
                    "instance_uuid": host_info['host'],
                    "connector": host_info,
                    "volume_uuid": volume_id
                }
            })
        result = requests.post(url, headers=self.admin_headers, data=data)
        return result

    def complete_attachment(self, attachment_id):
        url = self.cinder_url + self.project_id + '/attachments/' + \
              attachment_id + '/action'
        data = json.dumps({"os-complete": {}})
        result = requests.post(url, headers=self.admin_headers, data=data)
        return result

    def attach_volume(self, host_info, volume_id):
        attachment = self.create_attachment(host_info, volume_id)
        if attachment:
            self.complete_attachment(attachment.json()['attachment']['id'])
        return attachment

    def delete_attachment(self, attachment_id):
        url = self.cinder_url + self.project_id + '/attachments/' + \
              attachment_id
        result = requests.delete(url, headers=self.admin_headers)
        return result

    def detach_volume(self, volume_id, attachment_id):
        delete = self.delete_attachment(attachment_id)
        return delete

    def extend_volume(self, volume_id, new_size):
        url = self.cinder_url + self.project_id + '/volumes/' + volume_id + \
              '/action'
        data = json.dumps({
            "os-extend": {
                "new_size": int(new_size)
            }
        })
        result = requests.post(url, data=data, headers=self.admin_headers)
        return result

    def edit_volume(self, volume_id, new_volume_attr):
        url = self.cinder_url + self.project_id + '/volumes/' + volume_id
        data = json.dumps({
            "volume": new_volume_attr
        })
        result = requests.put(url, data=data, headers=self.admin_headers)
        return result

    def reset_status_volume(self, volume_id, new_status):
        url = self.cinder_url + self.project_id + '/volumes/' + volume_id + \
              '/action'
        if new_status == 'error':
            attach_status = 'detached'
            data = json.dumps({
                "os-reset_status": {
                    "status": new_status,
                    "attach_status": attach_status
                }
            })
        else:
            data = json.dumps({
                "os-reset_status": {
                    "status": new_status,
                }
            })
        result = requests.post(url, data=data, headers=self.admin_headers)
        return result

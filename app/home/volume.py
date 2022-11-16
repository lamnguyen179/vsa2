import json
from flask import render_template, request, redirect
from flask_login import login_required
from time import sleep

from app import const
from app import logger
from app.home import blueprint
from app.home import cinder_utils
from app.home import dcim_utils


VOLUME = cinder_utils.Volume(
    const.OPENSTACK_API_IP, const.OPENSTACK_CINDER_PORT,
    const.OPENSTACK_KEYSTONE_PORT, 'admin',
    'admin', const.OPENSTACK_ADMIN_PASSWORD
)
INSTANCE = dcim_utils.Instance(const.DCIM_API, const.DCIM_TOKEN)


def reset_status_volume(volume_id, new_status):
    result = VOLUME.reset_status_volume(volume_id, new_status)
    if result.status_code != 202:
        logger.error(f"Fail to reset status volume {volume_id} to {new_status}."
                     f" {result.content}")
    else:
        logger.info(f"Reset status volume {volume_id} to {new_status} "
                    f"successfully")
    return


@blueprint.route('/volume-admin', methods=['GET'])
@login_required
def volumes_admin():
    global VOLUME
    VOLUME = cinder_utils.Volume(
        const.OPENSTACK_API_IP, const.OPENSTACK_CINDER_PORT,
        const.OPENSTACK_KEYSTONE_PORT, 'admin',
        'admin', const.OPENSTACK_ADMIN_PASSWORD
    )
    all_volumes, all_volume_types = VOLUME.get_volumes_of_project()
    for v in all_volumes:
        host_list = []
        if v.get('attachments'):
            for atm in v['attachments']:
                host_list.append(atm['host_name'])
        host_list = ', '.join(host_list)
        all_volumes[all_volumes.index(v)]['host_list_string'] = host_list
    return render_template(
        'volume.html', volumes=all_volumes, volume_types=all_volume_types)


@blueprint.route('/volume-cloud', methods=['GET'])
@login_required
def volumes_cloud():
    global VOLUME
    VOLUME = cinder_utils.Volume(
        const.OPENSTACK_API_IP, const.OPENSTACK_CINDER_PORT,
        const.OPENSTACK_KEYSTONE_PORT, 'cloud',
        'cloud', const.OPENSTACK_CLOUD_PASSWORD)
    all_volumes, all_volume_types = VOLUME.get_volumes_of_project()
    for v in all_volumes:
        host_list = []
        if v.get('attachments'):
            for atm in v['attachments']:
                host_list.append(atm['host_name'])
        host_list = ', '.join(host_list)
        all_volumes[all_volumes.index(v)]['host_list_string'] = host_list
    return render_template(
        'volume.html', volumes=all_volumes, volume_types=all_volume_types)


@blueprint.route('/volume-physical', methods=['GET'])
@login_required
def volumes_physical():
    global VOLUME
    VOLUME = cinder_utils.Volume(
        const.OPENSTACK_API_IP, const.OPENSTACK_CINDER_PORT,
        const.OPENSTACK_KEYSTONE_PORT, 'physical',
        'physical', const.OPENSTACK_CLOUD_PASSWORD)
    all_volumes, all_volume_types = VOLUME.get_volumes_of_project()
    for v in all_volumes:
        host_list = []
        if v.get('attachments'):
            for atm in v['attachments']:
                host_list.append(atm['host_name'])
        host_list = ', '.join(host_list)
        all_volumes[all_volumes.index(v)]['host_list_string'] = host_list
    return render_template(
        'volume.html', volumes=all_volumes, volume_types=all_volume_types)


@blueprint.route('/get-volume-by-id', methods=['POST'])
@login_required
def get_volumes_by_id():
    volume_id = request.form['volume_id']
    volume = VOLUME.get_volumes_by_id(volume_id)
    if not volume:
        response = {'status': const.FAILED, 'msg': None}
        return json.dumps(response)
    if volume.get('attachments'):
        host_list = []
        for atm in volume['attachments']:
            host_list.append(atm['host_name'])
        host_list = ', '.join(host_list)
        volume['host_list_string'] = host_list
    response = {'status': const.SUCCESS, 'msg': volume}
    return json.dumps(response)


@blueprint.route('/delete-volume', methods=['POST'])
@login_required
def delete_volume():
    volume_id = request.form['volume_id']
    result = VOLUME.delete_volume(volume_id)
    if result.status_code != 202:
        logger.error(f"Fail to delete volume {volume_id}. {result.content}")
    else:
        logger.info(f"Delete volume {volume_id} successfully")
    return redirect(request.referrer)


@blueprint.route('/create-volume', methods=['POST'])
@login_required
def create_volume():
    size = request.form['volume_size']
    name = request.form['volume_name']
    volume_type = request.form['volume_type']
    result = VOLUME.create_volume(size, name, volume_type)
    if result.status_code != 202:
        logger.error(f"Fail to create volume {name}. {result.content}")
    else:
        logger.info(f"Create volume with name {name}, size {size} GiB, type "
                    f"{volume_type} successfully")
    return redirect(request.referrer)


@blueprint.route('/create-volume-with-attachment', methods=['POST'])
@login_required
def create_volume_and_attach():
    ip_address = request.form['host_ip']
    host_info = INSTANCE.get_host_info(ip_address)
    if not host_info:
        logger.error(f"Fail to create volume with attachment. Can not find "
                     f"host info with IP {ip_address}")
        return redirect(request.referrer)
    logger.info(f"Found host info with IP {ip_address}. {host_info}")
    size = 1
    name = request.form['volume_name']
    volume_type = request.form['volume_type']
    if not name:
        name = host_info['host'] + "_" + volume_type
    result_create = VOLUME.create_volume(size, name, volume_type)
    if result_create.status_code != 202:
        logger.error(f"Fail to create volume {name}. {result_create.content}")
        return redirect(request.referrer)
    logger.info(f"Create volume with name {name}, size {size} GiB, type "
                f"{volume_type} successfully")
    volume_id = result_create.json()['volume']['id']

    def wait_volume(w_volume_id):
        volume = VOLUME.get_volumes_by_id(w_volume_id)
        if not volume:
            logger.error(f"Can not find volume with id {w_volume_id}")
            return False
        status = volume['status']
        if status == 'available' or status == 'error':
            logger.info(f"Volume {w_volume_id} is {status}. Creating "
                        f"attachment")
            return True
        return False
    while not wait_volume(volume_id):
        logger.info(f"Volume not ready to attach. Sleeping 3s and check again")
        sleep(3)
    sleep(3)
    result_attach = VOLUME.attach_volume(host_info, volume_id)
    if result_attach.status_code != 200:
        logger.error(f"Fail to create attachment for volume {volume_id} and "
                     f"host {ip_address}. {result_attach.content}")
    else:
        logger.info(f"Create attachment for volume {volume_id} and host "
                    f"{ip_address} successfully")
        lock = request.form.get('lock_volume_atm')
        if lock:
            reset_status_volume(volume_id, 'locked')
    return redirect(request.referrer)


@blueprint.route('/get-host', methods=['POST'])
@login_required
def get_host_info_from_dcim():
    ip_address = request.form['host_ip']
    host_info = INSTANCE.get_host_info(ip_address)
    if not host_info:
        response = {'status': const.FAILED, 'msg': None}
    else:
        response = {'status': const.SUCCESS, 'msg': host_info}
    return json.dumps(response)


@blueprint.route('/attach-volume', methods=['POST'])
@login_required
def attach_volume():
    ip_address = request.form['host_ip']
    volume_id = request.form['volume_id']
    host_info = INSTANCE.get_host_info(ip_address)
    result = VOLUME.attach_volume(host_info, volume_id)
    if result.status_code != 200:
        logger.error(f"Fail to create attachment for volume {volume_id} and "
                     f"host {ip_address}. {result.content}")
    else:
        logger.info(f"Create attachment for volume {volume_id} and host "
                    f"{ip_address} successfully")
        lock = request.form.get('lock_volume_at')
        if lock:
            reset_status_volume(volume_id, 'locked')
    return redirect(request.referrer)


@blueprint.route('/detach-volume', methods=['POST'])
@login_required
def detach_volume():
    volume_id = request.form['volume_id']
    attachment_id = request.form['attachment_id']
    result = VOLUME.detach_volume(volume_id, attachment_id)
    if result.status_code != 200:
        logger.error(f"Fail to delete attachment {attachment_id} of volume "
                     f"{volume_id}. {result.content}")
    else:
        logger.info(f"Delete attachment {attachment_id} of volume {volume_id} "
                    f"successfully")
    return redirect(request.referrer)


@blueprint.route('/edit-volume', methods=['POST'])
@login_required
def edit_volume():
    volume_id = request.form['volume_id']
    new_volume_name = request.form['new_volume_name']
    new_volume_attr = {
        "name": str(new_volume_name),
    }
    result = VOLUME.edit_volume(volume_id, new_volume_attr)
    if result.status_code != 202:
        logger.error(f"Fail to edit volume {volume_id}. {result.content}")
    else:
        logger.info(f"Edit volume {volume_id} name to {new_volume_attr} "
                    f"successfully")
    return redirect(request.referrer)


@blueprint.route('/extend-volume', methods=['POST'])
@login_required
def extend_volume():
    volume_id = request.form['volume_id']
    new_volume_size = request.form['new_volume_size']
    result = VOLUME.extend_volume(volume_id, new_volume_size)
    if result.status_code != 202:
        logger.error(f"Fail to extend volume {volume_id}. {result.content}")
    else:
        logger.info(f"Extend volume {volume_id} size to {new_volume_size} "
                    f"successfully")
    return redirect(request.referrer)


@blueprint.route('/reset-status-volume', methods=['POST'])
@login_required
def reset_status():
    volume_id = request.form['volume_id']
    new_status = request.form['new_status']
    reset_status_volume(volume_id, new_status)
    return redirect(request.referrer)

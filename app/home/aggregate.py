import json
from flask import render_template, request, redirect
from flask_login import login_required

from app import const
from app import db, logger
from app.base import models
from app.home import blueprint
from app.home import cinder_utils, dcim_utils


INSTANCE = dcim_utils.Instance(const.DCIM_API, const.DCIM_TOKEN)


def add_server_to_aggregate(ip, aggregate_id):
    rsp = {
        "status": "",
        "msg": ""
    }
    server_check = models.Server.query.filter_by(ip=ip).first()
    if server_check:
        msg = f"Fail to add server {ip}. Server already existed"
        logger.error(msg)
        rsp['status'] = const.FAILED
        rsp['msg'] = msg
        return rsp

    agg_check = models.Aggregate.query.filter_by(id=aggregate_id).all()
    if not agg_check:
        msg = f"Fail to add server {ip}. Aggregate with id {aggregate_id} " \
              f"not found"
        logger.error(msg)
        rsp['status'] = const.FAILED
        rsp['msg'] = msg
        return rsp

    hostname = INSTANCE.get_host_hostname(ip)
    if not hostname:
        msg = f"Can not get server info with {ip} from DCIM"
        logger.error(msg)
        rsp['status'] = const.FAILED
        rsp['msg'] = msg
        return rsp

    server_add = models.Server(ip=ip, hostname=hostname,
                               aggregate_id=aggregate_id)
    db.session.add(server_add)
    db.session.commit()

    msg = f"Add server {ip} to aggregate {aggregate_id} successfully"
    logger.info(msg)
    rsp['status'] = const.SUCCESS
    rsp['msg'] = msg + '. F5 to view changes :D'
    return rsp


def add_storage_to_aggregate(name, aggregate_id):
    rsp = {
        "status": "",
        "msg": ""
    }
    storage_check = models.Storage.query.filter_by(name=name).first()
    if storage_check:
        msg = f"Fail to add storage {name}. Storage already existed"
        logger.error(msg)
        rsp['status'] = const.FAILED
        rsp['msg'] = msg
        return rsp

    agg_check = models.Aggregate.query.filter_by(id=aggregate_id).all()
    if not agg_check:
        msg = f"Fail to add storage {name}. Aggregate with id {aggregate_id} " \
              f"not found"
        logger.error(msg)
        rsp['status'] = const.FAILED
        rsp['msg'] = msg
        return rsp

    storage_add = models.Storage(name=name, aggregate_id=aggregate_id)
    db.session.add(storage_add)
    db.session.commit()

    msg = f"Add storage {name} to aggregate {aggregate_id} successfully"
    logger.info(msg)
    rsp['status'] = const.SUCCESS
    rsp['msg'] = msg + '. F5 to view changes :D'
    return rsp


def update_storage(name, new_name):
    rsp = {
        "status": "",
        "msg": ""
    }
    storage_check = models.Storage.query.filter_by(name=name).first()
    if not storage_check:
        msg = f"Fail to update storage. Storage with name {name} not found"
        logger.error(msg)
        rsp['status'] = const.FAILED
        rsp['msg'] = msg
        return rsp

    new_storage_check = models.Storage.query.filter_by(name=new_name).first()
    if new_storage_check:
        msg = f"Fail to update storage. Storage with new name {new_name} " \
              f"already existed"
        logger.error(msg)
        rsp['status'] = const.FAILED
        rsp['msg'] = msg
        return rsp

    storage_check.name = new_name
    db.session.commit()

    msg = f"Update storage {name} successfully"
    logger.info(msg)
    rsp['status'] = const.SUCCESS
    rsp['msg'] = msg + '. F5 to view changes :D'
    return rsp


def delete_storage(name):
    rsp = {
        "status": "",
        "msg": ""
    }
    storage_check = models.Storage.query.filter_by(name=name).first()
    if not storage_check:
        msg = f"Fail to delete storage. Storage with name {name} not found"
        logger.error(msg)
        rsp['status'] = const.FAILED
        rsp['msg'] = msg
        return rsp

    db.session.delete(storage_check)
    db.session.commit()

    msg = f"Delete storage {name} successfully"
    logger.info(msg)
    rsp['status'] = const.SUCCESS
    rsp['msg'] = msg + '. F5 to view changes :D'
    return rsp


def delete_server(ip):
    rsp = {
        "status": "",
        "msg": ""
    }
    server_check = models.Server.query.filter_by(ip=ip).first()
    if not server_check:
        msg = f"Fail to delete server. Server with IP {ip} not found"
        logger.error(msg)
        rsp['status'] = const.FAILED
        rsp['msg'] = msg
        return rsp

    db.session.delete(server_check)
    db.session.commit()

    msg = f"Delete server {ip} successfully"
    logger.info(msg)
    rsp['status'] = const.SUCCESS
    rsp['msg'] = msg + '. F5 to view changes :D'
    return rsp


@blueprint.route('/aggregate', methods=['GET'])
@login_required
def get_aggregate():
    all_aggregates = models.Aggregate.query.all()
    aggregates = []
    volume = cinder_utils.Volume(
        const.OPENSTACK_API_IP, const.OPENSTACK_CINDER_PORT,
        const.OPENSTACK_KEYSTONE_PORT, 'cloud',
        'cloud', const.OPENSTACK_CLOUD_PASSWORD)
    all_volumes, all_volume_types = volume.get_volumes_of_project()
    for agg in all_aggregates:
        storages = agg.storages
        storage_list = []
        if storages:
            for st in storages:
                storage_list.append(st.name)
        servers = agg.servers
        server_list = []
        if servers:
            for sv in servers:
                name = sv.hostname
                ip = sv.ip
                zoned = True
                for st in storage_list:
                    zoned = False
                    for volume in all_volumes:
                        if volume['volume_type'] == st \
                                and volume.get('attachments'):
                            for atm in volume['attachments']:
                                if atm.get('host_name') == name:
                                    zoned = True
                                    break
                            if zoned:
                                break
                server_list.append({
                    'ip': ip,
                    'hostname': name,
                    'zoned': zoned
                })

        agg_record = {
            'id': agg.id,
            'name': agg.name,
            'server_list': server_list,
            'storage_list': storage_list
        }
        aggregates.append(agg_record)
    return render_template('aggregate.html', aggregates=aggregates)


@blueprint.route('/add-aggregate', methods=['POST'])
@login_required
def add_aggregate():
    rsp = {
        "status": "",
        "msg": ""
    }
    agg_name = request.form['aggregate_name'].strip()
    host_list = request.form['hosts'].strip().split()
    storage_list = request.form['storages'].strip().split()
    agg_check = models.Aggregate.query.filter_by(name=agg_name).first()
    if agg_check:
        msg = f"Fail to create aggregate {agg_name}. Aggregate already existed"
        logger.error(msg)
        rsp['status'] = const.FAILED
        rsp['msg'] = msg
        return rsp

    agg_add = models.Aggregate(name=agg_name)
    db.session.add(agg_add)
    db.session.commit()

    if not host_list and not storage_list:
        msg = f"Create aggregate {agg_name} successfully"
        logger.info(msg)
        rsp['status'] = const.SUCCESS
        rsp['msg'] = msg + '. F5 to view changes :D'
        return rsp

    msg = f"Create aggregate {agg_name} successfully"
    status = const.SUCCESS
    new_agg_id = models.Aggregate.query.filter_by(name=agg_name).first().id
    if host_list:
        add_host_result = []
        for host in host_list:
            add_host_rsp = add_server_to_aggregate(host, new_agg_id)
            add_host_result.append({
                'ip': host,
                'result': add_host_rsp['status']
            })
        fail_host = []
        for rs in add_host_result:
            if rs['result'] == const.FAILED:
                fail_host.append(rs['ip'])
        if fail_host:
            fail_host_string = ', '.join(fail_host)
            msg += f". Fail to add {fail_host_string} to the new aggregate"
            status = const.WARN

    if storage_list:
        add_storage_result = []
        for storage in storage_list:
            add_storage_rsp = add_storage_to_aggregate(storage, new_agg_id)
            add_storage_result.append({
                'name': storage,
                'result': add_storage_rsp['status']
            })
        fail_storage = []
        for rs in add_storage_result:
            if rs['result'] == const.FAILED:
                fail_storage.append(rs['ip'])
        if fail_storage:
            fail_storage_string = ', '.join(fail_storage)
            msg += f". Fail to add {fail_storage_string} to the new aggregate"
            status = const.WARN
    rsp['status'] = status
    rsp['msg'] = msg
    if status == const.WARN:
        logger.warning(msg)
        return rsp
    logger.info(msg)
    return redirect(request.referrer)


@blueprint.route('/edit-aggregate', methods=['POST'])
@login_required
def edit_aggregate():
    rsp = {
        "status": "",
        "msg": ""
    }
    aggregate_id = request.form['edit_aggregate_id']
    new_aggregate_name = request.form['new_aggregate_name']
    agg_check = models.Aggregate.query.filter_by(id=aggregate_id).first()
    if not agg_check:
        msg = f"Fail to update aggregate. Aggregate with id {aggregate_id} " \
              f"not found"
        logger.error(msg)
        rsp['status'] = const.FAILED
        rsp['msg'] = msg
        return rsp

    new_agg_check = models.Aggregate.query.filter_by(
        name=new_aggregate_name).first()
    if new_agg_check:
        msg = f"Fail to update aggregate {aggregate_id} to new name " \
              f"{new_aggregate_name}. Aggregate already existed"
        logger.error(msg)
        rsp['status'] = const.FAILED
        rsp['msg'] = msg
        return rsp

    agg_check.name = new_aggregate_name
    db.session.commit()

    msg = f"Update aggregate {aggregate_id} successfully"
    logger.info(msg)
    rsp['status'] = const.SUCCESS
    rsp['msg'] = msg + '. F5 to view changes :D'
    return redirect(request.referrer)


@blueprint.route('/delete-aggregate', methods=['POST'])
@login_required
def delete_aggregate():
    rsp = {
        "status": "",
        "msg": ""
    }
    aggregate_id = request.form['delete_aggregate_id']
    agg_check = models.Aggregate.query.filter_by(id=aggregate_id).first()
    if not agg_check:
        msg = f"Fail to delete aggregate. Aggregate with id {aggregate_id} " \
              f"not found"
        logger.error(msg)
        rsp['status'] = const.FAILED
        rsp['msg'] = msg
        return rsp
    if agg_check.servers:
        for sv in agg_check.servers:
            delete_server(sv.ip)
    if agg_check.storages:
        for st in agg_check.storages:
            delete_storage(st.name)

    agg_check = models.Aggregate.query.filter_by(id=aggregate_id).first()
    if agg_check.servers or agg_check.storages:
        msg = f"Fail to delete aggregate. Aggregate with id {aggregate_id} " \
              f"still has some hosts or some storages could not be deleted"
        logger.error(msg)
        rsp['status'] = const.FAILED
        rsp['msg'] = msg
        return rsp

    db.session.delete(agg_check)
    db.session.commit()

    msg = f"Delete aggregate {aggregate_id} successfully"
    logger.info(msg)
    rsp['status'] = const.SUCCESS
    rsp['msg'] = msg + '. F5 to view changes :D'
    return redirect(request.referrer)


@blueprint.route('/add-server-to-aggregate', methods=['POST'])
@login_required
def add_server():
    list_server = request.form['servers'].strip().split()
    aggregate_id = request.form['server_aggregate_id']
    for sv in list_server:
        rsp = add_server_to_aggregate(sv, aggregate_id)
    return redirect(request.referrer)


@blueprint.route('/add-storage-to-aggregate', methods=['POST'])
@login_required
def add_storage():
    storages = request.form['storages']
    list_storage_name = storages.strip().split()
    aggregate_id = request.form['storage_aggregate_id']
    for name in list_storage_name:
        rsp = add_storage_to_aggregate(name, aggregate_id)
    return redirect(request.referrer)


@blueprint.route('/edit-storage', methods=['POST'])
@login_required
def edit_storage():
    storage_name = request.form['edit_storage']
    new_storage_name = request.form['new_storage_name']
    rsp = update_storage(storage_name, new_storage_name)
    return redirect(request.referrer)


@blueprint.route('/delete-storage', methods=['POST'])
@login_required
def del_storage():
    storage = request.form['delete_storage']
    rsp = delete_storage(storage)
    return redirect(request.referrer)


@blueprint.route('/delete-host', methods=['POST'])
@login_required
def del_server():
    server_ip_list = request.form.getlist('delete_host')
    for sv in server_ip_list:
        rsp = delete_server(sv)
    return redirect(request.referrer)

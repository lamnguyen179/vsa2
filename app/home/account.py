from flask import render_template, request
from flask_login import login_required

from app import const
from app import db, logger
from app.base import models
from app.home import blueprint


@blueprint.route('/account', methods=['GET', 'POST'])
@login_required
def accounts():
    accounts = models.Account.query.all()
    return render_template('account.html', accounts=accounts)


@blueprint.route('/get-account', methods=['GET'])
@login_required
def get_accounts():
    account_obj = models.Account.query.all()
    # TODO: fix here
    account_list = []
    for a in account_obj:
        account_list.append({
            'name': a.name,
            'api_key': a.api_key,
            'secret_key': a.secret_key
        })
    result = {
        "status": const.SUCCESS,
        "accounts": account_list
    }
    return result


@blueprint.route('/add-acc', methods=['POST'])
@login_required
def add_acc():
    rsp = {
        "status": "",
        "msg": ""
    }
    acc_name = request.form['acc_name']
    acc_api_key = request.form['acc_api_key']
    acc_secret_key = request.form['acc_secret_key']

    # Check acc name exists
    acc_check = models.Account.query.filter_by(name=acc_name).first()
    if acc_check:
        rsp['status'] = const.FAILED
        rsp['msg'] = 'Account with name: {} has existed!!!'.format(acc_name)
        return rsp
    # else we can create the acc
    acc_add = models.Account(name=acc_name, api_key=acc_api_key,
                             secret_key=acc_secret_key)
    db.session.add(acc_add)
    db.session.commit()

    logger.info("Create {} successfully!!!".format(acc_name))

    rsp['status'] = const.SUCCESS
    rsp['msg'] = 'Thêm acc: {} thành công. Reload lại trang để thấy!!!'.format(acc_name)
    return rsp


@blueprint.route('/edit-acc', methods=['PUT'])
@login_required
def edit_acc():
    rsp = {
        "status": "",
        "msg": ""
    }
    acc_name = request.form['acc_name']
    acc_api_key = request.form['acc_api_key']
    acc_secret_key = request.form['acc_secret_key']

    # Check usename exists
    acc_edit = models.Account.query.filter_by(name=acc_name).first()
    if not acc_edit:
        rsp['status'] = const.FAILED
        rsp['msg'] = 'Không thể tìm thấy acc: {}!!'.format(acc_name)
        return rsp

    # update information
    # acc_edit.name = acc_name
    acc_edit.api_key = acc_api_key
    acc_edit.secret_key = acc_secret_key
    db.session.commit()

    rsp['status'] = const.SUCCESS
    rsp['msg'] = 'Edit acc: {} thanh cong!!!'.format(acc_name)
    return rsp


@blueprint.route('/delete-acc', methods=['DELETE'])
@login_required
def delete_acc():
    rsp = {
        "status": "",
        "msg": ""
    }
    acc_name = request.form['acc_name']

    # Check usename exists
    acc_delete = models.Account.query.filter_by(name=acc_name).first()
    if not acc_delete:
        rsp['status'] = const.FAILED,
        rsp['msg'] = 'Khong the tim thay acc: {} de xoa!!!'.format(acc_name)
        return rsp

    # Lay danh sach Profile cua account
    profiles = models.Profile.query.filter_by(account_name=acc_name).all()
    if len(profiles):
        for p in profiles:
            db.session.delete(p)
            logger.info("Xoa profile {} theo account {} thành công!!!".format(
                p.account_name, acc_name))

    # delete
    db.session.delete(acc_delete)
    db.session.commit()

    logger.info("Delete acc {} successfully!!!".format(acc_name))

    rsp['status'] = const.SUCCESS
    rsp['msg'] = 'Xoa acc: {} thanh cong!!!'.format(acc_name)
    return rsp

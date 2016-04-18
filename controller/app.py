from flask import Blueprint, request, session
import json
from model.driver import driver_account
from model.adv import adv_info, adv_record
from app_config import db

app_bp = Blueprint('app', __name__)


@app_bp.route('/get_all_advs')
def get_all_adv():
    advs = adv_info.query.filter(adv_info.amounts > 0).all()
    ajax = []
    for adv in advs:
        dic = {}
        dic["adv_ID"] = adv.adv_ID
        dic["points"] = adv.location
        dic['flag'] = 'image'
        dic['image_src'] = adv.adv_pic
        ajax.append(dic)
    return json.dumps(ajax)


@app_bp.route('/check_login', methods=['POST', 'GET'])
def check_login():
    phone = request.form['phone']
    password = request.form['password']
    driver = driver_account.query.filter_by(phone=phone).first()
    result = {}
    if driver == None:
        result['status'] = 210
    else:
        if driver.check(password):
            session['driver_account_id'] = driver.account_ID
            session['driver_user_name'] = driver.user_name
            session['driver_account'] = driver.to_json()
            # 这里应该写个token
            result['status'] = 200
        else:
            result['status'] = 210
    return json.dumps(result)


@app_bp.route('/post_adv/<int:adv_ID>/<int:driver_account_ID>')
def post_adv(adv_ID, driver_account_ID):
    adv = adv_info.query.filter_by(adv_ID=adv_ID).first()
    adv.amounts -= 1
    record = adv_record(adv_ID, driver_account_ID)
    db.session.add(record)
    db.session.commit()
    return '200'

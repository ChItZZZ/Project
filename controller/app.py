from flask import Blueprint, request, session
import json
from flask import current_app
from model.driver import driver_account
from model.adv import adv_info, adv_record
from app_config import db
from tools.LBS import *
import time
from sqlalchemy import *
from controller.check_per import app_check_login
from tools.security import get_cap_code, get_salt
from ali_config import tool
from werkzeug.utils import secure_filename
import os

app = current_app
app_bp = Blueprint('app', __name__)


@app_bp.route('/check_register/', methods=['POST', 'GET'])
def check_register():
    try:
        user_id = request.values.get('userID')  # 身份证号
        phone = session['register_phone']
        user_name = request.values.get('user_name')  # 用户名
        password = request.values.get('password')  # 密码
        ID_card_image = request.files['ID_card_image']  # 身份证照片
        permit_card_image = request.files['permit_card_image']  # 驾驶证照片
        car_image = request.files['car_image']  # 行驶证照片
        ID_filename = secure_filename(ID_card_image.filename)
        permit_filename = secure_filename(permit_card_image.filename)
        ID_card_image.save(os.path.join(app.root_path, 'static/image/ID_card', ID_filename))
        permit_card_image.save(os.path.join(app.root_path, 'static/image/permit_card', permit_filename))
        car_pic_filename = secure_filename(car_image.filename)
        car_image.save(os.path.join(app.root_path, 'static/image/car', car_pic_filename))
        u = driver_account(phone, password, user_name, user_id, ID_filename, permit_filename, car_pic_filename)
        db.session.add(u)
        db.session.commit()
        return json.dumps({'status': '340'})
    except:
        return json.dumps({'status': '350'})


@app_bp.route('/check_register_code/', methods=['POST', 'GET'])
def check_register_code():
    check_code = session.get('register_code')
    if check_code != request.values.get('register_code'):
        return json.dumps({'status': '330'})
    else:
        return json.dumps({'status': '320'})


@app_bp.route('/get_register_code/<int:phone>/')
def get_register_code(phone):
    driver = driver_account.query.filter_by(phone=phone).first()
    if driver != None:
        return json.dumps({'status': '310'})  # 账号已经存在
    check_code = get_cap_code()
    session['register_code'] = check_code
    session['register_phone'] = str(phone)
    tool.send_register_message(phone, check_code)
    return json.dumps({'status': '300'})


@app_bp.route('/get_login_code/<int:phone>/')
def get_register_code(phone):
    driver = driver_account.query.filter_by(phone=phone).first()
    if driver == None:
        return json.dumps({'status': '210'})  # 账号不存在
    check_code = get_cap_code()
    session['login_code'] = check_code
    session['login_phone'] = str(phone)
    tool.send_register_message(phone, check_code)
    return json.dumps({'status': "300"})


@app_bp.route('/check_login_code/', methods=['POST', 'GET'])
def check_login_code():
    check_code = session.get('login_code')
    phone = session['login_phone']
    driver = driver_account.query.filter_by(phone=phone).first()
    if check_code != request.values.get('login_code'):
        session['driver_account_id'] = driver.account_ID
        session['driver_user_name'] = driver.user_name
        session['driver_account'] = driver.to_json()
        return json.dumps({'status': '330'})
    else:
        return json.dumps({'status': '320'})


@app_bp.route('/check_login', methods=['POST', 'GET'])
def check_login():
    phone = request.values.get('phone')
    password = request.values.get('password')
    driver = driver_account.query.filter_by(phone=phone).first()
    result = {}
    if driver == None:
        result['status'] = '210'
    else:
        if driver.check(password):
            session['driver_account_id'] = driver.account_ID
            session['driver_user_name'] = driver.user_name
            session['driver_account'] = driver.to_json()
            # 这里应该写个token
            result['status'] = '200'
        else:
            result['status'] = '210'
    return json.dumps(result)


@app_bp.route('/get_advs/<int:meter>/<float:lng>/<float:lat>/')
@app_check_login
def get_all_adv(meter, lat, lng):
    now = time.localtime(time.time())
    advs = adv_info.query.filter(and_(adv_info.amounts > 0, adv_info.start_date < now)).all()
    ajax = []
    for adv in advs:
        if adv.check_in(lat, lng, meter):
            dic = {}
            dic["adv_ID"] = adv.adv_ID
            dic["points"] = adv.location
            dic['flag'] = adv.img_flag
            dic['start_time'] = adv.start_time
            dic['end_time'] = adv.end_time
            dic['money'] = adv.cost
            if adv.img_flag:
                dic['img_src'] = adv.img_src
            else:
                dic['text'] = adv.adv_text
            ajax.append(dic)
    return json.dumps(ajax)


@app_bp.route('/post_adv/<int:adv_ID>/')
@app_check_login
def post_adv(adv_ID):
    driver_account_ID = session['driver_account_id']
    driver = driver_account.query.filter_by(account_ID=driver_account_ID).first()
    adv = adv_info.query.filter_by(adv_ID=adv_ID).first()
    if adv.amounts > 0:
        adv.amounts -= 1
        driver.account_money += adv.cost
        record = adv_record(adv_ID, driver_account_ID)
        db.session.add(record)
        db.session.commit()
        return json.dumps({'status': '400'})
    else:
        return json.dumps({'status': '410'})  # 广告发送失败


@app_bp.route('/get_driver_info/')
@app_check_login
def get_driver_info():
    driver = driver_account.query.filter_by(account_ID=session['driver_account_id']).first()
    return json.dumps(driver.to_json())


@app_bp.route('/get_records/')
@app_check_login
def get_records():
    account_ID = session['driver_account_id']
    records = adv_record.query.filter_by(driver_account_ID=account_ID).all()
    ajax = []
    i = 0
    for record in records:
        i += 1
        dic = {}
        adv = adv_info.query.filter_by(adv_ID=record.adv_ID).first()
        dic['adv_text'] = adv.adv_text
        dic['time'] = record.play_time.strftime("%Y-%m-%d %H:%M:%S")
        dic['money'] = float(adv.cost.real)
        ajax.append(dic)
        if (i == 25):
            break
    return json.dumps(ajax)

from flask import request, render_template, session, current_app, redirect, url_for, Blueprint
import os
from sqlalchemy import or_, and_
from werkzeug.utils import secure_filename
from model import db
from model.driver import driver_account
from model.sys_notice import sys_notice
from tools.security import get_cap_code, get_salt
from ali_config import tool
from controller.check_per import *
from model.adv import adv_record, adv_info
import json
import time

app = current_app
driver_bp = Blueprint('driver', __name__)


@driver_bp.route('/')
def index():
    if 'driver_account_id' not in session:
        return redirect(url_for('driver.login'))
    else:
        return redirect(url_for('driver.home'))


@driver_bp.route('/check_login', methods=['POST'])
def check_login():
    phone = request.form['phone']
    password = request.form['password']
    driver = driver_account.query.filter_by(phone=phone).first()
    if driver == None:
        return '<script>alert("用户名或密码错误");location.href="/driver/login"</script>'
    else:
        if driver.check(password):
            if driver.check_flag == None:
                session['flag'] = '未通过验证'
            elif driver.check_flag == False:
                return '<script>alert("账号被封禁");location.href="/driver/login"</script>'
            elif driver.check_flag == True:
                session['flag'] = '已通过验证'
            session['driver_account_id'] = driver.account_ID
            session['driver_user_name'] = driver.user_name
            session['driver_account'] = driver.to_json()
            session['phone'] = phone
            # 这里应该写个token
            return '<script>location.href="/driver/home"</script>'
        else:
            return '<script>alert("用户名或密码错误");location.href="/driver/login"</script>'


@driver_bp.route('/check_register', methods=['POST'])
def check_register():
    check_code = session.get('check_code')
    if check_code != request.form['check_code']:
        return '<script>alert("验证码错误!");location.href="/driver/register"</script>'
    user_id = request.form['userID']
    phone = session['register_phone']
    user_name = request.form['user_name']
    password = request.form['password']
    ID_card_image = request.files['ID_card_image']
    permit_card_image = request.files['permit_card_image']
    car_image = request.files['car_image']
    ID_filename = secure_filename(ID_card_image.filename)
    permit_filename = secure_filename(permit_card_image.filename)
    car_pic_filename = secure_filename(car_image.filename)
    filename = []
    filename.append(ID_filename)
    filename.append(permit_filename)
    filename.append(car_pic_filename)
    for f in filename:
        if '.' not in f or f.rsplit('.', 1)[1] not in app.config['ALLOW_FILE']:
            return '<script>alert("非法后缀!");location.href="/driver/register"</script>'
    ID_card_image.save(os.path.join(app.root_path, 'static/image/ID_card', ID_filename))
    permit_card_image.save(os.path.join(app.root_path, 'static/image/permit_card', permit_filename))
    car_image.save(os.path.join(app.root_path, 'static/image/car', car_pic_filename))
    u = driver_account(phone, password, user_name, user_id, ID_filename, permit_filename, car_pic_filename)
    db.session.add(u)
    db.session.commit()
    return '<script>alert("注册成功!");location.href="/driver/login"</script>'


@driver_bp.route('/login')
def login():
    return render_template('Drivers module/login.html')


@driver_bp.route('/register')
def register():
    return render_template('Drivers module/create-account.html')


@driver_bp.route('/get_check_code/<int:phone>')
def get_check_code(phone):
    driver = driver_account.query.filter_by(phone=phone).first()
    session['register_phone'] = str(phone)
    if driver != None:
        return '310'
    check_code = get_cap_code()
    session['check_code'] = check_code
    tool.send_register_message(phone, check_code)
    return "300"


@driver_bp.route('/forgot_pwd/')
def forgot_pwd():
    return render_template('Drivers module/forgot-password.html')


@driver_bp.route('/get_forgot_code/<int:phone>')
def get_forgot_code(phone):
    forget_code = get_cap_code()
    session['forget_code'] = forget_code
    session['phone_change'] = str(phone)
    tool.send_forgot_pwd_message(phone, forget_code)
    return "success"


@driver_bp.route('/check_forgot_code/', methods=['post'])
def check_forgot_pwd():
    code = request.form['code']
    phone = session['phone_change']
    if code == session['forget_code']:
        driver = driver_account.query.filter_by(phone=phone).first()
        pwd = get_salt(8)
        driver.change_pwd(pwd)
        return '<script>alert("您的新密码为{0},请登陆后尽快修改");location.href="/driver/login"</script>'.format(pwd)
    else:
        return '<script>alert("手机号或验证码有误,请重试")</script>'


@driver_bp.route('/home')
@driver_check_login
@driver_check_message
def home():
    driver = session['driver_account']
    return render_template('Drivers module/dri-home.html', name=session['driver_user_name'],
                           count=session['message_count'], phone=session['phone'], flag=session['flag'],
                           account=driver['account_money'], card_pic=driver['card_pic'], user_ID=driver['user_ID'])


@driver_bp.route('/security')
@driver_check_message
@driver_check_login
def security():
    return render_template('Drivers module/security.html', name=session['driver_user_name'],
                           count=session['message_count'], phone=session['phone'])


@driver_bp.route('/logout')
@driver_check_login
def logout():
    session.clear()
    return redirect(url_for('index'))


@driver_bp.route('/get_records/')
@driver_check_login
@driver_check_message
def get_records():
    account_ID = session['driver_account_id']
    records = adv_record.query.filter_by(driver_account_ID=account_ID).all()
    ajax = []
    i = 0
    for record in records:
        i += 1
        dic = {}
        adv = adv_info.query.filter_by(adv_ID=record.adv_ID).first()
        dic['NO'] = i
        dic['adv_text'] = adv.adv_sum
        dic['time'] = record.play_time.strftime("%Y-%m-%d %H:%M:%S")
        dic['money'] = float(adv.cost.real)
        ajax.append(dic)
        if (i == 25):
            break
    return json.dumps(ajax)


@driver_bp.route('/change_pwd/')
@driver_check_login
@driver_check_message
def change_pwd():
    return render_template('Drivers module/sec-modify-pwd-bypwd.html', name=session['driver_user_name'],
                           count=session['message_count'])


@driver_bp.route('/check_change_pwd/', methods=['POST'])
@driver_check_login
def check_change_pwd():
    old_pwd = request.form['old']
    new_pwd = request.form['new']
    driver = driver_account.query.get(session['driver_account_id'])
    if (driver.check(old_pwd)):
        driver.change_pwd(new_pwd)
        return '<script>alert("修改密码成功,请重新登录");location.href="/driver/logout"</script>'
    else:
        return '<script>alert("密码有误,请重试");location.href="/driver/change_pwd/";</script>'


@driver_bp.route('/get_message')
@driver_check_login
@driver_check_message
def get_message():
    driver_ID = session['driver_account_id']
    ms = message.query.filter(or_(and_(message.receiver_ID == driver_ID, message.flag == True),
                                  and_(message.sender_ID == driver_ID, message.flag == False))).all()
    ajax = []
    ms.reverse()
    for m in ms:
        ajax.append(m.to_json())
        if m.flag == True:
            m.read_flag = True
    db.session.commit()
    return json.dumps(ajax)


@driver_bp.route('/send_message/', methods=['POST'])
@driver_check_login
@driver_check_message
def send_message():
    text = request.form['text']
    receiver_ID = request.form['receiver_ID']
    sender_ID = session['driver_account_id']
    m = message(text, sender_ID, receiver_ID, False)
    db.session.add(m)
    db.session.commit()
    return 'success'


@driver_bp.route('/get_notice')
@driver_check_login
@driver_check_message
def get_notice():
    now = time.localtime(time.time())
    ajax = []
    ns = sys_notice.query.filter(
        and_(sys_notice.end_time > now, or_(sys_notice.notice_type == 3, sys_notice.notice_type == 1))).all()
    for n in ns:
        ajax.append(n.to_json())
    return json.dumps(ajax)


@driver_bp.route('/chat')
@driver_check_login
@driver_check_message
def chat():
    return render_template('Drivers module/dri-chat.html', name=session['driver_user_name'],
                           count=session['message_count'])


@driver_bp.route('/s_notice')
@driver_check_login
@driver_check_message
def s_notice():
    return render_template('Drivers module/notice.html', name=session['driver_user_name'],
                           count=session['message_count'])


@driver_bp.route('/ad_details')
@driver_check_login
@driver_check_message
def ad_details():
    account_ID = session['driver_account_id']
    record_count = adv_record.query.filter_by(driver_account_ID=account_ID).count()
    return render_template('Drivers module/ad-details.html', name=session['driver_user_name'],
                           count=session['message_count'], record_count=record_count)


@driver_bp.route('/get_records_by_page/<int:page>/')
@driver_check_login
@driver_check_message
def get_records_by_page(page):
    account_ID = session['driver_account_id']
    records = adv_record.query.filter_by(driver_account_ID=account_ID).all()
    ajax = []
    i = 0
    page -= 1
    records = records[10 * page:10 * page + 10]
    for record in records:
        dic = {}
        adv = adv_info.query.filter_by(adv_ID=record.adv_ID).first()
        dic['NO'] = i
        dic['adv_text'] = adv.adv_sum
        dic['time'] = record.play_time.strftime("%Y-%m-%d %H:%M:%S")
        dic['money'] = float(adv.cost.real)
        ajax.append(dic)
    return json.dumps(ajax)


@driver_bp.route('/get_cash/')
@driver_check_login
@driver_check_message
def get_cash():
    return render_template('Drivers module/get-cash.html', name=session['driver_user_name'],
                           count=session['message_count'])


@driver_bp.route('/get_money/<float:money>/', methods=['POST', 'GET'])
@driver_check_login
def get_money(money):
    driver = driver_account.query.filter_by(account_ID=session['driver_account_id']).first()
    pay_password = request.values.get('pay_pwd')
    if driver.check_pay_pwd(pay_password):
        if driver.money_change(-1 * money):
            session['driver_account'] = driver.to_json()
            return json.dumps({'status': '600'})  # 取款成功
        else:
            return json.dumps({'status': '610'})  # 余额不足
    else:
        return json.dumps({'status': '620'})  # 交易密码输入错误


@driver_bp.route('/change_pay_pwd/', methods=['POST', 'GET'])
@driver_check_login
@driver_check_message
def change_pay_pwd():
    return render_template('Drivers module/sec-modify-pay-pwd-bypwd.html', name=session['driver_user_name'],
                           count=session['message_count'])


@driver_bp.route('/check_change_pay_pwd/', methods=['POST'])
@driver_check_login
def check_change_pay_pwd():
    old_pwd = request.form['old']
    new_pwd = request.form['new']
    driver = driver_account.query.get(session['driver_account_id'])
    if (driver.check_pay_pwd(old_pwd)):
        driver.change_pay_pwd(new_pwd)
        return '<script>alert("修改支付密码成功!");location.href="/driver/home"</script>'
    else:
        return '<script>alert("密码有误,请重试");location.href="/driver/change_pay_pwd/";</script>'


@driver_bp.route('/find_pay_pwd/', methods=['POST', 'GET'])
@driver_check_login
@driver_check_message
def find_pay_pwd():
    return render_template('Drivers module/sec-find-pay-pwd.html', name=session['driver_user_name'],
                           count=session['message_count'], phone=session['phone'])

#
# @driver_bp.route('/change_phone/', methods=['POST', 'GET'])
# @driver_check_login
# @driver_check_message
# def change_phone():
#     return render_template('Drivers module/sec-phone.html', name=session['driver_user_name'],
#                            count=session['message_count'], phone=session['phone'])


@driver_bp.route('/get_forgot_pay_code/<int:phone>/')
@driver_check_login
def get_forgot_pay_code(phone):
    forget_code = get_cap_code()
    session['forget_code'] = forget_code
    tool.send_forgot_pay_message(phone, forget_code)
    return "success"


@driver_bp.route('/check_forgot_pay_code/', methods=['POST', 'GET'])
@driver_check_login
@driver_check_message
def check_forgot_pay_code():
    forgot_code = request.form['check_code']
    ID = request.form['user_ID']
    driver = driver_account.query.get(session['driver_account_id'])
    if (driver.user_ID == ID and forgot_code == session['forget_code']):
        session['forgot_pay_check_flag'] = True
        return render_template('Drivers module/sec-step2-pay.html', name=session['driver_user_name'],
                               count=session['message_count'])
    else:
        return '<script>alert("验证码或身份证号码有误,请重试");location.href="/driver/security";</script>'


@driver_bp.route('/check_forgot_pay_pwd/', methods=['POST', 'GET'])
@driver_check_login
@driver_check_message
def check_forgot_pay_pwd():
    if 'forgot_pay_check_flag' in session and session['forgot_pay_check_flag'] == True:
        new = request.form['new_pay_pwd']
        driver = driver_account.query.get(session['driver_account_id'])
        driver.change_pay_pwd(new)
        return '<script>alert("修改支付密码成功!");location.href="/driver/home"</script>'
    else:
        return '<script>alert("非法访问!");location.href="/driver/security";</script>'

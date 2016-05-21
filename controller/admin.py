from flask import request, render_template, session, redirect, url_for, Blueprint
from sqlalchemy import or_, and_, func
from model import db
from model.admin import admin_account
from model.adv import adv_info, adv_account, adv_record
from model.driver import driver_account
from model.message import message
from model.sys_notice import sys_notice
from tools.LBS import *
from controller.check_per import admin_check_login, admin_check_message
import json
import re

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/')
@admin_bp.route('/home')
@admin_bp.route('/index')
@admin_check_login
@admin_check_message
def index():
    return render_template('Management module/index.html', adm_name=session['admin_account_name'],
                           admin_message=session['admin_message'])


@admin_bp.route('/login')
def login():
    return render_template('Management module/login.html')


@admin_bp.route('/check_login', methods=['POST'])
def check_login():
    account_name = request.form['account']
    password = request.form['password']
    admin = admin_account.query.filter_by(account_name=account_name).first()
    if admin == None:
        return '<script>alert("用户名或密码错误");location.href="/admin/login"</script>'
    else:
        if admin.check(password):
            session['admin_account_id'] = admin.account_ID
            session['admin_account_name'] = admin.account_name
            return redirect(url_for('admin.index'))
        else:
            return '<script>alert("用户名或密码错误");location.href="/admin/login"</script>'


@admin_bp.route('/show_drivers')
@admin_check_login
@admin_check_message
def show_drivers():
    return render_template('Management module/drivers.html', adm_name=session['admin_account_name'],
                           admin_message=session['admin_message'])


@admin_bp.route('/drivers_ajax')
@admin_check_login
@admin_check_message
def drivers_ajax():
    drivers = driver_account.query.all()
    ajax = []
    for driver in drivers:
        dic = {}
        dic["account_ID"] = driver.account_ID
        dic["user_name"] = driver.user_name
        dic["phone"] = driver.phone
        dic["check_flag"] = str(driver.check_flag)
        m = message.query.filter(
            and_(message.sender_ID == driver.account_ID, message.flag == False, message.read_flag == False)).count()
        dic['red_point'] = m > 0
        ajax.append(dic)
    return json.dumps(ajax)


@admin_bp.route('/show_driver/<int:ID>')
@admin_check_login
@admin_check_message
def show_driver(ID):
    if ID == None:
        return redirect(url_for('admin.show_drivers'))
    else:
        driver = driver_account.query.filter_by(account_ID=ID).first()
        if driver == None:
            return redirect(url_for('admin.show_drivers'))
        return render_template('Management module/driver.html', phone=driver.phone, flag=str(driver.check_flag),
                               name=driver.user_name, user_id=driver.user_ID, permit_image=driver.permit_pic,
                               ID_card_image=driver.card_pic, adm_name=session['admin_account_name'],
                               admin_message=session['admin_message'], car_pic=driver.car_pic)


@admin_bp.route('/check_driver', methods=['GET'])
@admin_check_login
@admin_check_message
def check_driver():
    phone = request.args['phone']
    flag = bool(int(request.args['flag']))
    driver = driver_account.query.filter_by(phone=phone).first()
    driver.check_flag = flag
    db.session.commit()
    return "success"


@admin_bp.route('/show_advs')
@admin_check_login
@admin_check_message
def show_advs():
    return render_template('Management module/ads.html', adm_name=session['admin_account_name'],
                           admin_message=session['admin_message'])


@admin_bp.route('/advs_ajax')
@admin_check_login
@admin_check_message
def advs_ajax():
    advs = adv_info.query.all()
    ajax = []
    for adv in advs:
        dic = {}
        dic['adv_ID'] = adv.adv_ID
        dic['adv_amounts'] = adv.amounts
        dic['adv_text'] = adv.adv_text
        dic['cost'] = float(adv.cost.real)
        dic['date'] = str(adv.start_date)
        advter = adv_account.query.filter_by(account_ID=adv.advter_account_ID).first()
        dic['company'] = advter.company_name
        ajax.append(dic)
    return json.dumps(ajax)


@admin_bp.route('/adv/<int:adv_ID>')
@admin_check_login
@admin_check_message
def show_adv(adv_ID):
    if adv_ID == None:
        return redirect(url_for('admin.show_advs'))
    else:
        adv = adv_info.query.filter_by(adv_ID=adv_ID).first()
        advter = adv_account.query.filter_by(account_ID=adv.advter_account_ID).first()
        date = str(adv.start_time) + '-' + str(adv.end_time)
        location = []
        location_json = json.loads(adv.location)
        for point in location_json:
            location.append(gcj02tobd09(point[0], point[1]))
        return render_template('Management module/ad.html', adv_ID=adv.adv_ID, text=adv.adv_text, datetime=date,
                               location=location, company=advter.company_name, adm_name=session['admin_account_name'],
                               admin_message=session['admin_message'])


@admin_bp.route('/show_advters')
@admin_check_login
@admin_check_message
def show_advters():
    return render_template('Management module/adusers.html', adm_name=session['admin_account_name'],
                           admin_message=session['admin_message'])


@admin_bp.route('/advters_ajax')
@admin_check_login
@admin_check_message
def advters_ajax():
    advters = adv_account.query.all()
    ajax = []
    for advter in advters:
        dic = {}
        dic["account_ID"] = advter.account_ID
        dic["charge_name"] = advter.charge_name
        dic["company_name"] = advter.company_name
        dic["check_flag"] = str(advter.check_flag)
        ajax.append(dic)
    return json.dumps(ajax)


@admin_bp.route('/show_advter/<int:account_ID>')
@admin_check_login
@admin_check_message
def show_advter(account_ID):
    if account_ID == None:
        return redirect(url_for('admin.show_advters'))
    else:
        advter = adv_account.query.filter_by(account_ID=account_ID).first()
        return render_template('Management module/aduser.html', account_ID=account_ID, flag=advter.check_flag,
                               company=advter.company_name, amount=advter.adv_amount, name=advter.charge_name,
                               phone=advter.phone, remark=advter.remark, adm_name=session['admin_account_name'],
                               admin_message=session['admin_message'], company_img=advter.company_img,
                               ID_card=advter.ID_card)


@admin_bp.route('/check_advter', methods=['GET'])
@admin_check_login
@admin_check_message
def check_advter():
    account_ID = request.args['account_ID']
    flag = bool(int(request.args['flag']))
    advter = adv_account.query.filter_by(account_ID=account_ID).first()
    advter.check_flag = flag
    db.session.commit()
    return "success"


@admin_bp.route('/advs_history')
@admin_check_login
@admin_check_message
def advs_history():
    return render_template('Management module/ads_history.html', adm_name=session['admin_account_name'],
                           admin_message=session['admin_message'])


@admin_bp.route('/drivers_history')
@admin_check_login
@admin_check_message
def drivers_history():
    return render_template('Management module/drivers_history.html', adm_name=session['admin_account_name'],
                           admin_message=session['admin_message'])


@admin_bp.route('/driver_history/<int:driver_ID>')
@admin_check_login
@admin_check_message
def driver_history(driver_ID):
    driver = driver_account.query.filter_by(account_ID=driver_ID).first()
    return render_template('Management module/driver_history.html', account_ID=driver.account_ID, name=driver.user_name,
                           phone=driver.phone, flag=driver.check_flag, adm_name=session['admin_account_name'],
                           admin_message=session['admin_message'])


@admin_bp.route('/get_records_by_driver/<int:driver_ID>/')
@admin_check_login
@admin_check_message
def get_records_by_driver(driver_ID):
    records = adv_record.query.filter_by(driver_account_ID=driver_ID).all()
    ajax = []
    date_dic = {}
    for record in records:
        dic = {}
        dic['adv_ID'] = record.adv_ID
        dic['time'] = record.play_time.strftime("%Y-%m-%d %H:%M:%S")
        date = record.play_time.strftime("%Y-%m-%d")
        if date not in date_dic:
            date_dic[date] = 1
        else:
            date_dic[date] += 1
        ajax.append(dic)
    for a in ajax:
        a['times'] = date_dic[re.findall('[0-9]+\-[0-9]+\-[0-9]+', a['time'])[0]]
    return json.dumps(ajax)


@admin_bp.route('/adv_history/<int:adv_ID>')
@admin_check_login
@admin_check_message
def adv_history(adv_ID):
    adv = adv_info.query.filter_by(adv_ID=adv_ID).first()
    last_time = '{0}至{1}'.format(adv.start_time.strftime('%H:%M:%S'), adv.end_time.strftime('%H:%M:%S'))
    advter = adv_account.query.filter_by(account_ID=adv.advter_account_ID).first()
    return render_template('Management module/ad_history.html', adv_ID=adv_ID, last_time=last_time,
                           company=advter.company_name, adm_name=session['admin_account_name'],
                           admin_message=session['admin_message'])


@admin_bp.route('/get_records_by_adv/<int:adv_ID>/')
@admin_check_login
@admin_check_message
def get_records_by_adv(adv_ID):
    records = adv_record.query.filter_by(adv_ID=adv_ID).all()
    result = {'word': [], 'chart': {}}
    ajax1 = []
    dic2 = {}
    for record in records:
        dic1 = {}
        dic1['driver_ID'] = record.driver_account_ID
        dic1['time'] = record.play_time.strftime("%Y-%m-%d %H:%M:%S")
        ajax1.append(dic1)
        if record.play_time.strftime("%Y.%m.%d") not in dic2:
            dic2[record.play_time.strftime("%Y.%m.%d")] = 1
        else:
            dic2[record.play_time.strftime("%Y.%m.%d")] += 1
    result['word'] = ajax1
    result['chart'] = dic2

    return json.dumps(result)


@admin_bp.route('/chat/<int:receiver_ID>')
@admin_check_login
@admin_check_message
def chat(receiver_ID):
    name = driver_account.query.filter_by(account_ID=receiver_ID).first().user_name
    return render_template('Management module/chat.html', receiver_ID=receiver_ID, name=name,
                           adm_name=session['admin_account_name'], admin_message=session['admin_message'])


@admin_bp.route('/chats')
@admin_bp.route('/chats.html')
@admin_check_login
@admin_check_message
def chats():
    return render_template('Management module/chats.html', adm_name=session['admin_account_name'],
                           admin_message=session['admin_message'])


@admin_bp.route('/get_message/<int:driver_ID>')
@admin_check_login
@admin_check_message
def get_message(driver_ID):
    ms = message.query.filter(or_(and_(message.receiver_ID == driver_ID, message.flag == True),
                                  and_(message.sender_ID == driver_ID, message.flag == False))).all()
    ajax = []
    ms.reverse()
    for m in ms:
        if m.flag == False:
            m.read_flag = True
        ajax.append(m.to_json())
    db.session.commit()
    return json.dumps(ajax)


@admin_bp.route('/send_message/', methods=['POST'])
@admin_check_login
@admin_check_message
def send_message():
    text = request.form['text']
    receiver_ID = request.form['receiver_ID']
    sender_ID = session['admin_account_id']
    m = message(text, sender_ID, receiver_ID, True)
    db.session.add(m)
    db.session.commit()
    return 'success'


@admin_bp.route('/notice')
@admin_check_login
@admin_check_message
def notice():
    return render_template('Management module/notice.html', adm_name=session['admin_account_name'],
                           admin_message=session['admin_message'])


@admin_bp.route('/send_notice', methods=['POST'])
@admin_check_login
@admin_check_message
def send_notice():
    title = request.form['title']
    text = request.form['text']
    type = request.form['optionsRadios']
    date = request.form['date']
    type_dic = {'allusers': 1, 'adusers': 2, 'drivers': 3}
    n = sys_notice(title, text, type_dic[type], date)
    db.session.add(n)
    db.session.commit()
    return '<script>alert("发布成功!");location.href="/admin/notice"</script>'


@admin_bp.route('/logout')
@admin_check_login
def logout():
    session.clear()
    return redirect(url_for('admin.login'))


@admin_bp.route('/get_notice')
@admin_check_login
@admin_check_message
def get_notice():
    ns = sys_notice.query.all()
    ajax = []
    for n in ns:
        dic = n.to_json()
        ajax.append(dic)
    return json.dumps(ajax)

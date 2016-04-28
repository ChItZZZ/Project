from flask import request, render_template, session, redirect, url_for, Blueprint

from model import db
from model.admin import admin_account
from model.adv import adv_info, adv_account, adv_record
from model.driver import driver_account
from tools.LBS import *
from controller.check_per import admin_check_login
import json
import re

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/')
@admin_bp.route('/home')
@admin_bp.route('/index.html')
@admin_check_login
def index():
    return render_template('Management module/index.html', name=session['admin_account_name'])


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
def show_drivers():
    return render_template('Management module/drivers.html')


@admin_bp.route('/drivers_ajax')
@admin_check_login
def drivers_ajax():
    drivers = driver_account.query.all()
    ajax = []
    for driver in drivers:
        dic = {}
        dic["account_ID"] = driver.account_ID
        dic["user_name"] = driver.user_name
        dic["phone"] = driver.phone
        dic["check_flag"] = str(driver.check_flag)
        ajax.append(dic)
    return str(ajax)


@admin_bp.route('/show_driver/<int:ID>')
@admin_check_login
def show_driver(ID):
    if ID == None:
        return redirect(url_for('admin.show_drivers'))
    else:
        driver = driver_account.query.filter_by(account_ID=ID).first()
        return render_template('Management module/driver.html', phone=driver.phone, flag=str(driver.check_flag),
                               name=driver.user_name, user_id=driver.user_ID, permit_image=driver.permit_pic,
                               ID_card_image=driver.card_pic)


@admin_bp.route('/check_driver', methods=['GET'])
@admin_check_login
def check_driver():
    phone = request.args['phone']
    flag = bool(int(request.args['flag']))
    driver = driver_account.query.filter_by(phone=phone).first()
    driver.check_flag = flag
    db.session.commit()
    return "success"


@admin_bp.route('/show_advs')
@admin_check_login
def show_advs():
    return render_template('Management module/ads.html')


@admin_bp.route('/advs_ajax')
@admin_check_login
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
    return str(ajax)


@admin_bp.route('/adv/<int:adv_ID>')
@admin_check_login
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
                               location=location, company=advter.company_name)


@admin_bp.route('/show_advters')
@admin_check_login
def show_advters():
    return render_template('Management module/adusers.html')


@admin_bp.route('/advters_ajax')
@admin_check_login
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
def show_advter(account_ID):
    if account_ID == None:
        return redirect(url_for('admin.show_advters'))
    else:
        advter = adv_account.query.filter_by(account_ID=account_ID).first()
        return render_template('Management module/aduser.html', account_ID=account_ID, flag=advter.check_flag,
                               company=advter.company_name, amount=advter.adv_amount, name=advter.charge_name,
                               phone=advter.phone, remark=advter.remark)


@admin_bp.route('/check_advter', methods=['GET'])
@admin_check_login
def check_advter():
    account_ID = request.args['account_ID']
    flag = bool(int(request.args['flag']))
    advter = adv_account.query.filter_by(account_ID=account_ID).first()
    advter.check_flag = flag
    db.session.commit()
    return "success"


@admin_bp.route('/advs_history')
def advs_history():
    return render_template('Management module/ads_history.html')


@admin_bp.route('/drivers_history')
def drivers_history():
    return render_template('Management module/drivers_history.html')


@admin_bp.route('/driver_history/<int:driver_ID>')
def driver_history(driver_ID):
    driver = driver_account.query.filter_by(account_ID=driver_ID).first()
    return render_template('Management module/driver_history.html', account_ID=driver.account_ID, name=driver.user_name,
                           phone=driver.phone, flag=driver.check_flag)


@admin_bp.route('/get_records_by_driver/<int:driver_ID>/')
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
def adv_history(adv_ID):
    adv = adv_info.query.filter_by(adv_ID=adv_ID).first()
    last_time = '{0}至{1}'.format(adv.start_time.strftime('%H:%M:%S'), adv.end_time.strftime('%H:%M:%S'))
    advter = adv_account.query.filter_by(account_ID=adv.advter_account_ID).first()
    return render_template('Management module/ad_history.html', adv_ID=adv_ID, last_time=last_time,
                           company=advter.company_name)


@admin_bp.route('/get_records_by_adv/<int:adv_ID>/')
def get_records_by_adv(adv_ID):
    records = adv_record.query.filter_by(adv_ID=adv_ID).all()
    ajax = []
    for record in records:
        dic = {}
        dic['driver_ID'] = record.driver_account_ID
        dic['time'] = record.play_time.strftime("%Y-%m-%d %H:%M:%S")
        ajax.append(dic)
    return json.dumps(ajax)

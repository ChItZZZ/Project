from flask import Blueprint, render_template, request, session, redirect, url_for, current_app
from model.adv import *
from model.driver import *
from tools.LBS import *
from tools.security import *
from ali_config import tool
from controller.check_per import advter_check_login
from datetime import datetime
from werkzeug.utils import secure_filename
import os
from model.sys_notice import sys_notice
from sqlalchemy import *

app = current_app
adv_bp = Blueprint('adv', __name__)


@adv_bp.route('/')
def index():
    if 'adv_charge_name' not in session:
        return redirect(url_for('adv.login'))
    else:
        return redirect(url_for('adv.home'))


@adv_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@adv_bp.route('/check_login', methods=['POST'])
def check_login():
    phone = request.form['phone']
    password = request.form['password']
    advter = adv_account.query.filter_by(phone=phone).first()
    if advter == None:
        return '<script>alert("用户名或密码错误");location.href="/adv/login"</script>'
    else:
        if advter.check(password):
            if advter.check_flag == None:
                session['flag'] = '未通过验证'
            elif advter.check_flag == False:
                return '<script>alert("账号被封禁");location.href="/adv/login"</script>'
            else:
                session['flag'] = '已通过验证'
            session['adv_account_id'] = advter.account_ID
            session['adv_charge_name'] = advter.charge_name
            session['phone'] = advter.phone
            session['money'] = float(advter.account_money)
            # 这里应该写个token
            return '<script>location.href="/adv/home"</script>'
        else:
            return '<script>alert("用户名或密码错误");location.href="/adv/login"</script>'


@adv_bp.route('/register/')
def register():
    return render_template('Advertiser module/create-account.html')


@adv_bp.route('/check_register/', methods=['POST', 'GET'])
def check_register():
    check_code = session.get('check_code')
    if check_code != request.form['check_code']:
        return '<script>alert("验证码错误!");location.href="/adv/register"</script>'
    user_id = request.form['userID']
    phone = session['register_phone']
    company_name = request.form['company_name']
    user_name = request.form['user_name']
    password = request.form['password']
    ID_card_image = request.files['ID_card_image']
    company_img = request.files['company_img']
    ID_filename = secure_filename(ID_card_image.filename)
    company_img_filename = secure_filename(company_img.filename)
    filename = []
    filename.append(company_img_filename)
    filename.append(ID_filename)
    for f in filename:
        if '.' not in f or f.rsplit('.', 1)[1] not in app.config['ALLOW_FILE']:
            return '<script>alert("非法后缀!");location.href="/adv/login"</script>'
    ID_card_image.save(os.path.join(app.root_path, 'static/image/ID_card', ID_filename))
    company_img.save(os.path.join(app.root_path, 'static/image/company', company_img_filename))
    u = adv_account(password, company_name, user_name, phone, company_img_filename, ID_filename, user_id)
    db.session.add(u)
    db.session.commit()
    return '<script>alert("注册成功!");location.href="/adv/login"</script>'


@adv_bp.route('/get_check_code/<int:phone>')
def get_check_code(phone):
    advter = adv_account.query.filter_by(phone=phone).first()
    if advter != None:
        return '310'
    session['register_phone'] = str(phone)
    check_code = get_cap_code()
    session['check_code'] = check_code
    tool.send_register_message(phone, check_code)
    return "300"


@adv_bp.route('/forgot_pwd/')
def forgor_pwd():
    return render_template('Advertiser module/forgot-password.html')


@adv_bp.route('/get_forgot_code/<int:phone>')
def get_forgot_code(phone):
    adv = adv_account.query.filter_by(phone=phone)
    session['phone_change'] = str(phone)
    if adv == None:
        return '315'
    forget_code = get_cap_code()
    session['forget_code'] = forget_code
    tool.send_forgot_pwd_message(phone, forget_code)
    return "300"


@adv_bp.route('/check_forgot_code/', methods=['POST'])
def check_forgot_code():
    code = request.form['code']
    phone = session['phone_change']
    if code == session['forget_code']:
        advter = adv_account.query.filter_by(phone=phone).first()
        pwd = get_salt(8)
        advter.change_pwd(pwd)
        return '<script>alert("您的新密码为{0},请登陆后尽快修改");location.href="/adv/login"</script>'.format(pwd)
    else:
        return '<script>alert("手机号或验证码有误,请重试");location.href="/adv/forgot_pwd"</script>'


@adv_bp.route('/check_adv_submit', methods=['POST'])
@advter_check_login
def check_adv_submit():
    flag = request.form['select'] == 'true'
    adv_count = int(request.form['adv_count'])
    location = json.loads(request.form['location'])
    gcj02_loc = []
    for point in location:
        gcj02_loc.append(bd09togcj02(point[0], point[1]))
    loc = {'type': '1', 'points': gcj02_loc}  # type为1为多边形
    if len(json.dumps(loc)) > 500:
        return '<script>alert("选择点过多请重试");location.href="/adv/adv_submit_one/"</script>'
    date = datetime.strptime(request.form['date'], '%m/%d/%Y')
    start_time = time.strptime(request.form['start_time'], '%H:%M')
    end_time = time.strptime(request.form['end_time'], '%H:%M')
    cost = float(request.form['cost'])
    adv_sum = request.form['adv_sum']
    advter = adv_account.query.filter_by(account_ID=session['adv_account_id']).first()
    if not advter.check_pay_pwd(request.form['pay-password']):
        return '<script>alert("交易密码输入有误");location.href="/adv/adv_submit"</script>'
    if advter.check_flag == None or advter.check_flag == False:
        return '<script>alert("尚未通过验证");location.href="/adv/home"</script>'
    if flag:
        img = request.files['adv_img']
        img_filename = secure_filename(img.filename)
        if '.' not in img_filename or img_filename.rsplit('.', 1)[1] not in app.config['ALLOW_FILE']:
            return '<script>alert("非法后缀!");location.href="/adv/adv_submit"</script>'
        img.save(os.path.join(app.root_path, 'static/image/adv_img', img_filename))
        adv = adv_info(cost, adv_count, date, start_time, end_time, loc, session['adv_account_id'], adv_sum, flag,
                       img_src=img_filename)
    else:
        adv_text = request.form['adv_text']
        adv = adv_info(cost, adv_count, date, start_time, end_time, loc, session['adv_account_id'], adv_sum, flag,
                       adv_text)
    if not advter.money_change(-1 * cost * adv_count):
        return '<script>alert("账号余额不足");location.href="/adv/home"</script>'
    else:
        session['money'] = float(advter.account_money)
    db.session.add(adv)
    db.session.commit()
    his = adv_history(adv.adv_ID, session['adv_account_id'], cost * adv_count)
    db.session.add(his)
    db.session.commit()
    return '<script>alert("发布成功");location.href="/adv/home"</script>'


@adv_bp.route('/adv_submit')
@advter_check_login
def adv_submit():
    return render_template('Advertiser module/ad-sub-sel.html', name=session['adv_charge_name'])


@adv_bp.route('/adv_submit_one/')
@advter_check_login
def adv_submit_one():
    return render_template('Advertiser module/ad-submit.html', name=session['adv_charge_name'])


@adv_bp.route('/advs_submit_many/')
@advter_check_login
def advs_submit_many():
    return render_template('Advertiser module/advs-submit.html', name=session['adv_charge_name'])


@adv_bp.route('/check_advs_submit_many/', methods=['POST', 'GET'])
@advter_check_login
def check_advs_submit_many():
    flag = request.form['select'] == 'true'
    adv_count = int(request.form['adv_count'])
    location = json.loads(request.form['location'])
    gcj02_loc = []
    for point in location:
        gcj02_loc.append(bd09togcj02(point[0], point[1]))
    range = request.form['range']
    remark = request.form['remark']
    center = json.loads(request.form['center'])
    center = bd09togcj02(center[0], center[1])
    loc = {'type': '0', 'points': gcj02_loc, 'range': range}  # type为1为多边形
    if len(json.dumps(loc)) > 500:
        return '<script>alert("选择地点过多请重试");location.href="/adv/advs_submit_many/"</script>'
    date = datetime.strptime(request.form['date'], '%m/%d/%Y')
    start_time = time.strptime(request.form['start_time'], '%H:%M')
    end_time = time.strptime(request.form['end_time'], '%H:%M')
    cost = float(request.form['cost'])
    adv_sum = request.form['adv_sum']
    advter = adv_account.query.filter_by(account_ID=session['adv_account_id']).first()
    if not advter.check_pay_pwd(request.form['pay-password']):
        return '<script>alert("交易密码输入有误");location.href="/adv/advs_submit_many/"</script>'
    if advter.check_flag == None or advter.check_flag == False:
        return '<script>alert("尚未通过验证");location.href="/adv/home"</script>'
    if flag:
        img = request.files['adv_img']
        img_filename = secure_filename(img.filename)
        if '.' not in img_filename or img_filename.rsplit('.', 1)[1] not in app.config['ALLOW_FILE']:
            return '<script>alert("非法后缀!");location.href="/adv/advs_submit_many/"</script>'
        img.save(os.path.join(app.root_path, 'static/image/adv_img', img_filename))
        adv = adv_info(cost, adv_count, date, start_time, end_time, loc, session['adv_account_id'], adv_sum, flag,
                       img_src=img_filename, remark=remark, center=center)
    else:
        adv_text = request.form['adv_text']
        adv = adv_info(cost, adv_count, date, start_time, end_time, loc, session['adv_account_id'], adv_sum, flag,
                       adv_text, remark=remark, center=center)
    if not advter.money_change(-1 * cost * adv_count):
        return '<script>alert("账号余额不足");location.href="/adv/home"</script>'
    else:
        session['money'] = float(advter.account_money)
    db.session.add(adv)
    db.session.commit()
    his = adv_history(adv.adv_ID, session['adv_account_id'], cost * adv_count)
    db.session.add(his)
    db.session.commit()
    return '<script>alert("发布成功");location.href="/adv/home"</script>'


@adv_bp.route('/login')
def login():
    return render_template('Advertiser module/login.html')


@adv_bp.route('/home/')
@advter_check_login
def home():
    return render_template('Advertiser module/adv-home.html', name=session['adv_charge_name'], phone=session['phone'],
                           money=session['money'], flag=session['flag'])


@adv_bp.route('/get_rec_price/<float:lat>/<float:lng>/')
@advter_check_login
def get_rec_price(lat, lng):
    lng, lat = bd09togcj02(lng, lat)
    advs = adv_info.query.all()
    rec_price = 0
    times = 0
    for adv in advs:
        center = json.loads(adv.center)
        dis = get_distance(lat, lng, center[1], center[0])
        if dis < 1:
            rec_price += dis * float(adv.cost)
            times += dis
    if times == 0:
        return '0.05'
    else:
        return str(round(rec_price / times, 3))


@adv_bp.route('/security')
@advter_check_login
def security():
    return render_template('Advertiser module/security.html', name=session['adv_charge_name'], phone=session['phone'])


@adv_bp.route('/get_history')
@advter_check_login
def get_history():
    historys = adv_history.query.filter_by(advter_ID=session['adv_account_id']).order_by(adv_history.adv_ID.desc()).all()
    ajax = []
    for h in historys:
        ajax.append(h.to_json())
        if len(ajax) == 25:
            break
    return json.dumps(ajax)


@adv_bp.route('/change_pwd')
@advter_check_login
def change_pwd():
    return render_template('Advertiser module/sec-modify-pwd-bypwd.html', name=session['adv_charge_name'])


@adv_bp.route('/check_change_pwd/', methods=['POST'])
@advter_check_login
def check_change_pwd():
    old_pwd = request.form['old']
    new_pwd = request.form['new']
    advter = adv_account.query.get(session['adv_account_id'])
    if (advter.check(old_pwd)):
        advter.change_pwd(new_pwd)
        return '<script>alert("修改密码成功,请重新登录");location.href="/adv/logout"</script>'
    else:
        return '<script>alert("密码有误,请重试");location.reload();</script>'


@adv_bp.route('/notice')
@advter_check_login
def notice():
    return render_template('Advertiser module/notice.html', name=session['adv_charge_name'])


@adv_bp.route('/get_notice')
@advter_check_login
def get_notice():
    now = time.localtime(time.time())
    ajax = []
    ns = sys_notice.query.filter(
        and_(sys_notice.end_time > now, or_(sys_notice.notice_type == 1, sys_notice.notice_type == 2))).all()
    for n in ns:
        ajax.append(n.to_json())
    return json.dumps(ajax)


@adv_bp.route('/change_phone')
@advter_check_login
def change_phone():
    return render_template('Advertiser module/sec-phone.html')


@adv_bp.route('/pay/<float:money>/')
@advter_check_login
def pay(money):
    advter = adv_account.query.filter_by(account_ID=session['adv_account_id']).first()
    advter.money_change(money)
    session['money'] = float(advter.account_money.real)
    return '<script>alert("充值成功!");location.href="/adv/home"</script>'


@adv_bp.route('/change_pay_pwd/', methods=['POST', 'GET'])
@advter_check_login
def change_pay_pwd():
    return render_template('Advertiser module/sec-modify-pay-pwd-bypwd.html', name=session['adv_charge_name'])


@adv_bp.route('/check_change_pay_pwd/', methods=['POST'])
@advter_check_login
def check_change_pay_pwd():
    old_pwd = request.form['old']
    new_pwd = request.form['new']
    advter = adv_account.query.get(session['adv_account_id'])
    if (advter.check_pay_pwd(old_pwd)):
        advter.change_pay_pwd(new_pwd)
        return '<script>alert("修改支付密码成功!");location.href="/adv/home"</script>'
    else:
        return '<script>alert("密码有误,请重试");location.reload();</script>'


@adv_bp.route('/find_pay_pwd/', methods=['POST', 'GET'])
@advter_check_login
def find_pay_pwd():
    return render_template('Advertiser module/sec-find-pay-pwd.html', name=session['adv_charge_name'],
                           phone=session['phone'])


@adv_bp.route('/get_forgot_pay_code/<int:phone>/')
@advter_check_login
def get_forgot_pay_code(phone):
    forget_code = get_cap_code()
    session['forget_code'] = forget_code
    tool.send_forgot_pay_message(phone, forget_code)
    return "success"


@adv_bp.route('/check_forgot_pay_code/', methods=['POST', 'GET'])
@advter_check_login
def check_forgot_pay_code(phone):
    forgot_code = request.form['forget_code']
    ID = request.form['ID']
    advter = adv_account.query.get(session['adv_account_id'])
    if (advter.user_ID == ID and forgot_code == session['forget_code']):
        return render_template('Advertiser module/')
    else:
        return '<script>alert("验证码或身份证号码有误,请重试");location.href="/adv/security";</script>'


@adv_bp.route('/ad_list/')
@adv_bp.route('/ad_history/')
@adv_bp.route('/delete_adv/')
@adv_bp.route('/ad_details/')
@advter_check_login
def ad_list():
    return render_template('Advertiser module/ad-list.html', name=session['adv_charge_name'])


@adv_bp.route('/ad_list_ajax/')
@advter_check_login
def ad_list_ajax():
    advter_ID = session['adv_account_id']
    advs = adv_info.query.filter_by(advter_account_ID=advter_ID).all()
    advs.reverse()
    ajax = []
    for adv in advs:
        history = adv_history.query.filter_by(adv_ID=adv.adv_ID).first()
        dic = adv.to_json()
        dic['post_time'] = str(history.post_time)
        ajax.append(dic)
    return json.dumps(ajax)


@adv_bp.route('/delete_adv/<int:adv_ID>/')
@advter_check_login
def delete_adv(adv_ID):
    adv = adv_info.query.get(adv_ID)
    if adv == None or adv.advter_account_ID != session['adv_account_id']:
        return redirect(url_for('adv.ad_list'))
    session['money'] = adv.del_adv()
    return '<script>alert("广告已被删除,余款已退回");location.href="/adv/ad_list/";</script>'


@adv_bp.route('/ad_history/<int:adv_ID>/')
@advter_check_login
def ad_history(adv_ID):
    adv = adv_info.query.get(adv_ID)
    if adv == None or adv.advter_account_ID != session['adv_account_id']:
        return redirect(url_for('adv.ad_list'))
    return render_template('Advertiser module/ad-history.html', name=session['adv_charge_name'], adv_ID=adv_ID)


@adv_bp.route('/ad_history_ajax/<int:adv_ID>/<int:record_ID>/')
@advter_check_login
def ad_history_ajax(adv_ID, record_ID):
    adv = adv_info.query.get(adv_ID)
    if adv == None or adv.advter_account_ID != session['adv_account_id']:
        return json.dumps({'error': '无权限'})
    else:
        records = adv_record.query.filter(
            and_(adv_record.adv_ID == adv_ID, adv_record.record_ID > record_ID)).order_by(
            adv_record.record_ID.desc()).limit(10).all()
        ajax = []
        for record in records:
            driver = driver_account.query.get(record.driver_account_ID)
            dic = record.to_json()
            dic['phone'] = driver.phone
            dic['user_name'] = driver.user_name
            ajax.append(dic)
        return json.dumps(ajax)


@adv_bp.route('/ad_details/<int:adv_ID>/')
@advter_check_login
def ad_details(adv_ID):
    adv = adv_info.query.get(adv_ID)
    if adv == None or adv.advter_account_ID != session['adv_account_id']:
        return redirect(url_for('adv.ad_list'))
    return render_template('Advertiser module/ad-details.html', name=session['adv_charge_name'], adv_ID=adv_ID)


@adv_bp.route('/ad_details_ajax/<int:adv_ID>/')
@advter_check_login
def ad_details_ajax(adv_ID):
    adv = adv_info.query.get(adv_ID)
    if adv == None or adv.advter_account_ID != session['adv_account_id']:
        return json.dumps({'error': '无权限'})
    else:
        return json.dumps(adv.get_details())

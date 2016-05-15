from flask import Blueprint, render_template, request, session, redirect, url_for, current_app
from model.adv import *
from tools.LBS import *
from tools.security import *
from ali_config import tool
from controller.check_per import advter_check_login
from datetime import datetime
from werkzeug.utils import secure_filename
import os

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
    return redirect(url_for('adv.login'))


@adv_bp.route('/check_login', methods=['POST'])
def check_login():
    phone = request.form['phone']
    password = request.form['password']
    advter = adv_account.query.filter_by(phone=phone).first()
    if advter == None:
        return '<script>alert("用户名或密码错误");location.href="login"</script>'
    else:
        if advter.check(password):
            session['adv_account_id'] = advter.account_ID
            session['adv_charge_name'] = advter.charge_name
            session['phone'] = advter.phone
            # 这里应该写个token
            return '<script>location.href="/adv/home"</script>'
        else:
            return '<script>alert("用户名或密码错误");location.href="login"</script>'


@adv_bp.route('/register/')
def register():
    return render_template('Advertiser module/create-account.html')


@adv_bp.route('/check_register/', methods=['POST', 'GET'])
def check_register():
    check_code = session['check_code']
    if check_code != request.form['check_code']:
        return '<script>alert("验证码错误!");location.href="/adv/register"</script>'
    user_id = request.form['userID']
    phone = request.form['phone']
    company_name = request.form['company_name']
    user_name = request.form['user_name']
    password = request.form['password']
    ID_card_image = request.files['ID_card_image']
    company_img = request.files['company_img']
    ID_filename = secure_filename(ID_card_image.filename)
    company_img_filename = secure_filename(company_img.filename)
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
    if adv == None:
        return '310'
    forget_code = get_cap_code()
    session['forget_code'] = forget_code
    session['phone'] = phone
    tool.send_forgot_pwd_message(phone, forget_code)
    return "300"


@adv_bp.route('/check_forgot_code/')
def check_forgot():
    pass


@adv_bp.route('/check_adv_submit', methods=['POST'])
@advter_check_login
def check_adv_submit():
    flag = request.form['select'] == 'true'
    adv_count = int(request.form['adv_count'])
    location = json.loads(request.form['location'])
    gcj02_loc = []
    for point in location:
        gcj02_loc.append(bd09togcj02(point[0], point[1]))
    date = datetime.strptime(request.form['date'], '%m/%d/%Y')
    start_time = time.strptime(request.form['start_time'], '%H:%M')
    end_time = time.strptime(request.form['end_time'], '%H:%M')
    cost = float(request.form['cost'])
    adv_sum = request.form['adv_sum']
    if flag:
        img = request.files['adv_img']
        img_filename = secure_filename(img.filename)
        img.save(os.path.join(app.root_path, 'static/image/adv_img', img_filename))
        adv = adv_info(cost, adv_count, date, start_time, end_time, location, session['adv_account_id'], adv_sum, flag,
                       img_filename)
    else:
        adv_text = request.form['adv_text']
        adv = adv_info(cost, adv_count, date, start_time, end_time, location, session['adv_account_id'], adv_sum, flag,
                       adv_text)

    db.session.add(adv)
    db.session.commit()
    his = adv_history(adv.adv_ID, session['adv_account_id'], cost * adv_count)
    db.session.add(his)
    db.session.commit()
    return '<script>alert("发布成功");location.href="home"</script>'


@adv_bp.route('/adv_submit')
@advter_check_login
def adv_submit():
    return render_template('Advertiser module/ad-submit.html', name=session['adv_charge_name'])


@adv_bp.route('/login')
def login():
    return render_template('Advertiser module/login.html')


@adv_bp.route('/home/')
@advter_check_login
def home():
    return render_template('Advertiser module/adv-home.html', name=session['adv_charge_name'], phone=session['phone'])


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
            rec_price += (1 - dis) * float(adv.cost.real)
            times += (1 - dis)
    if times == 0:
        return '0.05'
    else:
        return str(rec_price / max(times, 1))


@adv_bp.route('/security')
@advter_check_login
def security():
    return render_template('Advertiser module/security.html', name=session['adv_charge_name'], phone=session['phone'])


@adv_bp.route('/get_history')
@advter_check_login
def get_history():
    historys = adv_history.query.filter_by(advter_ID=session['adv_account_id']).all()
    ajax = []
    for h in historys:
        ajax.append(h.to_json())
    return json.dumps(ajax)


@adv_bp.route('/change_pwd')
@advter_check_login
def change_pwd():
    return render_template('Advertiser module/sec-modify-pwd-bypwd.html')


@adv_bp.route('/change_pay_pwd')
@advter_check_login
def change_pay_pwd():
    return render_template('Advertiser module/sec-modify-pwd-bypwd.html')


@adv_bp.route('/change_phone')
@advter_check_login
def change_phone():
    return render_template('Advertiser module/sec-phone.html')


@adv_bp.route('/find_pay_pwd')
@advter_check_login
def find_pay_pwd():
    phone = session['phone']
    return render_template('Advertiser module/sec-find-pay-pwd.html', phone=phone)


@adv_bp.route('/adv_details')
@advter_check_login
def task_details():
    return render_template('Advertiser module/')

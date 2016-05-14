from flask import Blueprint, render_template, request, session, redirect, url_for, current_app
from model.adv import *
from tools.LBS import *
from controller.check_per import advter_check_login
from datetime import datetime

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
            # 这里应该写个token
            return '<script>location.href="/adv/home"</script>'
        else:
            return '<script>alert("用户名或密码错误");location.href="login"</script>'


@adv_bp.route('/check_adv_submit', methods=['POST'])
@advter_check_login
def check_adv_submit():
    adv_text = request.form['adv_text']
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
    adv = adv_info(cost, adv_count, date, start_time, end_time, gcj02_loc, session['adv_account_id'], adv_text,
                   adv_sum)
    db.session.add(adv)
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
    return render_template('Advertiser module/adv-home.html', name=session['adv_charge_name'])


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

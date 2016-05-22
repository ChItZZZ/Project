from app_config import db
import hashlib
import time
from tools.LBS import get_distance, gcj02tobd09
import json
from tools import security
import datetime


class adv_info(db.Model):
    __tablename__ = 'adv_info'
    adv_ID = db.Column('adv_ID', db.Integer, primary_key=True, nullable=False, autoincrement=True)
    cost = db.Column('cost', db.DECIMAL(6, 3), nullable=False)
    amounts = db.Column('amounts', db.Integer, nullable=False)
    start_date = db.Column('start_date', db.Date, nullable=False)
    start_time = db.Column('start_time', db.Time, nullable=False)
    end_time = db.Column('end_time', db.Time, nullable=False)
    location = db.Column('location', db.String(500), nullable=False)
    advter_account_ID = db.Column('advter_account_ID', db.Integer, nullable=False)
    adv_sum = db.Column('adv_sum', db.String(50))
    adv_text = db.Column('adv_text', db.String(80))
    check_flag = db.Column('check_flag', db.Boolean)
    img_src = db.Column('img_src', db.String(50))
    img_flag = db.Column('img_flag', db.Boolean)
    center = db.Column('center', db.String(40))
    remark = db.Column('remark', db.String(50))

    def __init__(self, cost, amounts, start_date, start_time, end_time, location, advter_account_ID, adv_sum, img_flag,
                 adv_text=None, img_src=None, remark=None):
        self.cost = cost
        self.amounts = amounts
        self.start_date = start_date
        self.start_time = start_time
        self.end_time = end_time
        self.location = json.dumps(location)
        self.advter_account_ID = advter_account_ID
        self.adv_text = adv_text
        self.adv_sum = adv_sum
        self.check_flag = None
        self.img_flag = img_flag
        self.img_src = img_src
        lat_all = 0
        lng_all = 0
        if location['type'] == '1':
            location = location['points']
            for point in location:
                lng_all += point[0]
                lat_all += point[1]
            center = [lng_all / len(location), lat_all / len(location)]
        else:
            center = location['points'][0]
        self.center = str(center)
        self.remark = remark

    def check_in(self, lat, lng, meter):
        points = json.loads(self.location)
        for point in points:
            if get_distance(lat, lng, point[1], point[0]) < meter / 1000.0:
                return True
        return False

    def check_time(self):
        now = time.strptime(time.strftime('%H:%M:%S'), '%H:%M:%S')
        start = time.strptime(str(self.start_time), '%H:%M:%S')
        end = time.strptime(str(self.end_time), '%H:%M:%S')
        if now >= start and now <= end:
            return True
        else:
            return False

    def to_json(self):
        dic = {}
        dic['adv_ID'] = self.adv_ID
        dic['adv_amounts'] = self.amounts
        dic['adv_sum'] = self.adv_sum
        dic['cost'] = float(self.cost.real)
        dic['date'] = str(self.start_date)
        advter = adv_account.query.filter_by(account_ID=self.advter_account_ID).first()
        dic['company'] = advter.company_name
        check_flag = {None: '未审核', True: '审核通过', False: '审核不通过'}
        dic['check_flag'] = check_flag[self.check_flag]
        if self.remark == None:
            dic['remark'] = '无'
        else:
            dic['remark'] = self.remark
        return dic

    def get_details(self):
        dic = {}
        dic['adv_ID'] = self.adv_ID
        dic['img_flag'] = self.img_flag
        if self.img_flag:
            dic['img_src'] = self.img_src
        else:
            dic['adv_text'] = self.adv_text
        dic['time'] = str(self.start_time) + '-' + str(self.end_time)
        dic['adv_amounts'] = self.amounts
        location_json = json.loads(self.location)
        points = location_json['points']
        dic['type'] = location_json['type']
        if location_json['type'] == '1':
            location = []
            for point in points:
                location.append(gcj02tobd09(point[0], point[1]))
            dic['location'] = json.dumps(location)
        else:
            dic['range'] = points[1]
        advter = adv_account.query.filter_by(account_ID=self.advter_account_ID).first()
        dic['company_name'] = advter.company_name
        center = json.loads(self.center)
        dic['center'] = json.dumps(gcj02tobd09(center[0], center[1]))
        if self.remark == None:
            dic['remark'] = '无'
        else:
            dic['remark'] = self.remark
        return dic

    def check_adv(self, check_flag):
        if self.check_flag == None:
            self.check_flag = check_flag
            if not check_flag:  # 审核不过要退费
                advter = adv_account.query.get(self.advter_account_ID)
                advter.money_change(self.cost * self.amounts)
            db.session.commit()
            return True
        else:
            return False  # 已经被审核过的不能再改变

    def del_adv(self):
        advter = adv_account.query.get(self.advter_account_ID)
        if self.check_flag != False:
            advter.money_change(self.cost * self.amounts)
        db.session.delete(self)
        db.session.commit()
        return float(advter.account_money)


class adv_account(db.Model):
    __tablename__ = 'adv_account'
    account_ID = db.Column('account_ID', db.Integer, primary_key=True, nullable=False, autoincrement=True)
    salt = db.Column('salt', db.String(16), nullable=False)
    account_pwd = db.Column('account_pwd', db.String(40), nullable=False)
    company_name = db.Column('company_name', db.String(40), nullable=False)
    adv_amount = db.Column('adv_amount', db.Integer, nullable=False)
    charge_name = db.Column('charge_name', db.String(18), nullable=False)
    phone = db.Column('phone', db.String(11), nullable=False)
    company_img = db.Column('company_img', db.String(50))
    ID_card = db.Column('ID_card', db.String(50))
    user_ID = db.Column('user_ID', db.String(50))
    check_flag = db.Column('check_flag', db.Boolean)
    remark = db.Column('remark', db.String(50))
    pay_password = db.Column('pay_password', db.String(50))
    account_money = db.Column('account_money', db.DECIMAL(10, 3), nullable=False, default=0)

    def __init__(self, account_pwd, company_name, charge_name, phone, company_img, ID_card, user_ID):
        self.salt = security.get_salt(16)
        self.account_pwd = hashlib.md5((account_pwd + self.salt).encode('ascii')).hexdigest()
        self.company_name = company_name
        self.charge_name = charge_name
        self.phone = phone
        self.company_img = company_img
        self.ID_card = ID_card
        self.user_ID = user_ID
        self.adv_amount = 0
        self.pay_password = hashlib.md5((account_pwd + self.salt).encode('ascii')).hexdigest()

    def check(self, password):
        password = hashlib.md5((password + self.salt).encode('ascii')).hexdigest()
        if password == self.account_pwd:
            return True
        else:
            return False

    def change_pwd(self, pwd):
        self.account_pwd = hashlib.md5((pwd + self.salt).encode('ascii')).hexdigest()
        db.session.commit()
        return True

    def check_pay_pwd(self, pwd):
        password = hashlib.md5((pwd + self.salt).encode('ascii')).hexdigest()
        if password == self.pay_password:
            return True
        else:
            return False

    def change_pay_pwd(self, password):
        password = hashlib.md5((password + self.salt).encode('ascii')).hexdigest()
        self.pay_password = password
        db.session.commit()
        return True

    def to_json(self):
        dic = {}
        check_flag = {None: '未审核', True: '审核通过', False: '被封禁'}
        dic["account_ID"] = self.account_ID
        dic["charge_name"] = self.charge_name
        dic["company_name"] = self.company_name
        dic["check_flag"] = check_flag[self.check_flag]
        return dic

    def money_change(self, money):  # 正为增加钱 负为扣费
        if float(self.account_money) + float(money) > 0:
            self.account_money = float(self.account_money) + float(money)
            db.session.commit()
            return True
        else:
            return False


class adv_record(db.Model):
    __tablename__ = 'adv_record'
    record_ID = db.Column('record_ID', db.Integer, primary_key=True, nullable=False, autoincrement=True)
    adv_ID = db.Column('adv_ID', db.Integer, nullable=False)
    driver_account_ID = db.Column('driver_account_ID', db.Integer, nullable=False)
    play_time = db.Column('play_time', db.DateTime, nullable=False)

    def __init__(self, adv_ID, driver_account_ID):
        self.adv_ID = adv_ID
        self.driver_account_ID = driver_account_ID
        self.play_time = time.localtime()

    def check_play(self, second):  # 判断是否可以再次播放这条广告
        now = datetime.datetime.now()
        record_time = self.play_time.tm_hour + datetime.timedelta(seconds=second)
        if now <= record_time:
            return False
        else:
            return True

    def to_json(self):
        dic = {}
        dic['record_ID'] = self.record_ID
        dic['adv_ID'] = self.adv_ID
        dic['driver_account_ID'] = self.driver_account_ID
        dic['play_time'] = str(self.play_time)
        return dic


class adv_history(db.Model):
    __tablename__ = 'adv_history'
    history_ID = db.Column('history_ID', db.Integer, primary_key=True, nullable=False, autoincrement=True)
    adv_ID = db.Column('adv_ID', db.Integer, nullable=False)
    advter_ID = db.Column('advter_ID', db.Integer, nullable=False)
    cost = db.Column('cost', db.DECIMAL(10, 3), nullable=False)
    post_time = db.Column('post_time', db.Date, nullable=False)

    def __init__(self, adv_ID, advter_ID, cost):
        self.adv_ID = adv_ID
        self.advter_ID = advter_ID
        self.post_time = time.localtime()
        self.cost = cost

    def to_json(self):
        dic = {}
        dic['adv_ID'] = self.adv_ID
        dic['post_time'] = str(self.post_time)
        dic['cost'] = float(self.cost.real)
        dic['history'] = self.history_ID
        return dic

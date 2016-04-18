from app_config import db
import hashlib
import time


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
    adv_pic = db.Column('adv_pic', db.String(50))
    adv_text = db.Column('adv_text', db.String(80))
    check_flag = db.Column('check_flag', db.Boolean)

    def __init__(self, cost, amounts, start_date, start_time, end_time, location, advter_account_ID, adv_text,
                 adv_pic=None):
        self.cost = cost
        self.amounts = amounts
        self.start_date = start_date
        self.start_time = start_time
        self.end_time = end_time
        self.location = location
        self.advter_account_ID = advter_account_ID
        self.adv_text = adv_text
        self.adv_pic = adv_pic
        self.check_flag = None


class adv_account(db.Model):
    __tablename__ = 'adv_account'
    account_ID = db.Column('account_ID', db.Integer, primary_key=True, nullable=False, autoincrement=True)
    salt = db.Column('salt', db.String(16), nullable=False)
    account_pwd = db.Column('account_pwd', db.String(40), nullable=False)
    company_name = db.Column('company_name', db.String(40), nullable=False)
    adv_amount = db.Column('adv_amount', db.Integer, nullable=False)
    charge_name = db.Column('charge_name', db.String(18), nullable=False)
    phone = db.Column('phone', db.String(11), nullable=False)
    check_flag = db.Column('check_flag', db.Boolean)
    remark = db.Column('remark', db.String(50))

    def check(self, password):
        password = hashlib.md5((password + self.salt).encode('ascii')).hexdigest()
        if password == self.account_pwd:
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

from app_config import db
import time
import datetime


class sys_notice(db.Model):
    __tablename__ = 'notice'
    notice_ID = db.Column('notice_ID', db.Integer, primary_key=True, nullable=False, autoincrement=True)
    notice_title = db.Column('notice_title', db.String(50), nullable=False)
    notice_text = db.Column('notice_text', db.String(255), nullable=False)
    notice_type = db.Column('notice_type', db.Integer, nullable=False)
    start_time = db.Column('start_date', db.DateTime, nullable=False)
    end_time = db.Column('end_date', db.DateTime, nullable=False)

    def __init__(self, title, text, type, end_time):
        self.notice_title = title
        self.notice_text = text
        self.notice_type = type
        self.start_time = time.localtime(time.time())
        self.end_time = datetime.datetime.strptime(end_time, '%Y-%m-%d')

    def to_json(self):
        dic = {}
        dic['ID'] = self.notice_ID
        dic['title'] = self.notice_title
        dic['start_time'] = self.start_time.strftime("%Y-%m-%d")
        dic['end_time'] = self.end_time.strftime("%Y-%m-%d")
        dic['text']=self.notice_text
        return dic

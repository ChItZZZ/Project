from app_config import db
import time

class message(db.Model):
    __tablename__ = 'message'
    message_ID = db.Column('message_ID', db.Integer, primary_key=True, nullable=False, autoincrement=True)
    message_text = db.Column('message_text', db.String(500), nullable=False)
    sender_ID = db.Column('sender_ID', db.Integer, nullable=False)
    receiver_ID = db.Column('receiver_ID', db.Integer, nullable=False)
    send_time = db.Column('send_time', db.DateTime, nullable=False)
    flag = db.Column('flag', db.Integer, nullable=False)  # True是由管理员到用户 false是用户到管理员

    def __init__(self, text, sender_ID, receiver_ID, flag):
        self.message_text = text
        self.sender_ID = sender_ID
        self.receiver_ID = receiver_ID
        self.flag = flag
        self.send_time = time.localtime(time.time())


    def to_json(self):
        dic = {}
        dic['message_text'] = self.message_text
        dic['flag'] = self.flag
        dic['time'] = self.send_time.strftime("%Y-%m-%d %H:%M:%S")
        dic['sender_ID'] = self.sender_ID
        return dic

from app_config import db
from model.driver import driver_account


class message(db.Model):
    __tablename__ = 'message'
    message_ID = db.Column('message_ID', db.Integer, primary_key=True, nullable=False, autoincrement=True)
    message_text = db.Column('message_text', db.String(500), nullable=False)
    sender_ID = db.Column('sender_ID', db.Integer, nullable=False)
    receiver_ID = db.Column('receiver_ID', db.Integer, nullable=False)
    receiver_name = db.Column('receiver_name', db.String(18), nullable=False)

    def __init__(self, text, sender_ID, receiver_ID):
        self.message_text = text
        self.sender_ID = sender_ID
        self.receiver_ID = receiver_ID
        name = driver_account.query.filter_by(account_ID=receiver_ID).first().user_name
        self.receiver_name = name

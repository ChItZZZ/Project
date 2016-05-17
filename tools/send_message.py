# coding=utf-8
import top


class ali_message_tools:
    req = None

    def __init__(self, app_key, secret, url='http://gw.api.taobao.com/router/rest'):
        self.req = top.api.AlibabaAliqinFcSmsNumSendRequest(url)
        self.req.set_app_info(top.appinfo(app_key, secret))

    def set_para(self, sms_free_sign_name, sms_param, rec_num, sms_template_code):
        # self.req.extend = "123456"
        self.req.sms_type = "normal"
        self.req.sms_free_sign_name = sms_free_sign_name
        self.req.sms_param = str(sms_param)
        self.req.rec_num = rec_num
        self.req.sms_template_code = sms_template_code

    def send_message(self):
        try:
            resp = self.req.getResponse()
            return resp
        except Exception as e:
            return e

    def send_register_message(self, phone, code):
        sms_param = {"product": "MovineAD", "code": code}
        self.set_para("注册验证", sms_param, phone, "SMS_7495113")
        return self.send_message()

    def send_forgot_pwd_message(self, phone, code):
        sms_param = {"product": "MovineAD", "code": code}
        self.set_para("变更验证", sms_param, phone, "SMS_7495111")
        return self.send_message()

    def send_forgot_pay_message(self, phone, code):
        sms = {'product': "MovingAD支付密码", "code": code}
        self.set_para('变更验证', sms, phone, 'SMS_7495110')
        return self.send_message()

    def send_login_message(self, phone, code):
        sms_param = {"product": "MovineAD", "code": code}
        self.set_para("登录验证", sms_param, phone, "SMS_7495115")
        return self.send_message()

import random
import string


def get_salt(num):
    salt = ''.join(random.sample(string.ascii_letters + string.digits, num))
    return salt


def get_cap_code():
    code = str(random.randint(0, 9999))
    zero_length = 4 - len(code)
    return '0' * zero_length + code


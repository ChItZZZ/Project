from functools import wraps
from flask import redirect, url_for, session


def admin_check_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_account_id' not in session:
            return redirect(url_for('admin.login'))
        else:
            return f(*args, **kwargs)

    return decorated_function


def driver_check_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'driver_account_id' not in session:
            return redirect(url_for('driver.login'))
        else:
            return f(*args, **kwargs)

    return decorated_function


def advter_check_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'adv_account_id' not in session:
            return redirect(url_for('adv.login'))
        else:
            return f(*args, **kwargs)

    return decorated_function

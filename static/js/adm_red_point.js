/**
 *
 * Created by haha370104 on 16/5/18.
 */
//新消息标题栏闪烁显示
var newMessageRemind = {
    _step: 0,
    _title: document.title,
    _timer: null,

    //显示新消息提示
    show: function () {
        var temps = newMessageRemind._title.replace("【　　　】", "").replace("【新消息】", "");
        newMessageRemind._timer = setTimeout(function () {
                newMessageRemind.show();

                //这里写Cookie操作
                newMessageRemind._step++;
                if (newMessageRemind._step == 3) {
                    newMessageRemind._step = 1
                }
                if (newMessageRemind._step == 1) {
                    document.title = "【　　　】" + temps
                }
                if (newMessageRemind._step == 2) {
                    document.title = "【新消息】" + temps
                }
            },
            800);
        return [newMessageRemind._timer, newMessageRemind._title];
    },

    //取消新消息提示
    clear: function () {
        clearTimeout(newMessageRemind._timer);
        document.title = newMessageRemind._title;
        //这里写Cookie操作
    }
};

//newMessageRemind.show();  // *********************************显示新消息标题栏闪烁提示 调用此函数

function clearNewMessageRemind() {    //**********************取消新消息标题栏闪烁提示 调用此函数
    newMessageRemind.clear();
    location.href='/admin/show_drivers';
}

//管理员ID旁边小红点

function showredspot() {		// *********************************显示小红点调用此函数
    document.getElementById("redspot").style.display = "block";
}

function hideredspot() {		// *********************************隐藏小红点调用此函数
    document.getElementById("redspot").style.display = "none";
}

function show_red_point(flag) {
    if (flag == 'True') {
        newMessageRemind.show();
        showredspot();
    }
}

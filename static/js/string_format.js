/**
 *
 * Created by haha370104 on 16/5/22.
 */


String.prototype.format = function () {
    var args = arguments;
    return this.replace(/\{(\d+)\}/g,
        function (m, i) {
            return args[i];
        });
}
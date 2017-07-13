jQuery.fn.copyText = function(){
console.log(this);
    if (document.body.createTextRange) {
        var range = document.body.createTextRange();
        range.moveToElementText(this[0]);
        range.select();
    } else if (window.getSelection) {
        var selection = window.getSelection();
        var range = document.createRange();
        range.selectNodeContents(this[0]);
        selection.removeAllRanges();
        console.log(selection, range);
        selection.addRange(range);
        console.log(selection, range);
    }
    if (!document.execCommand("copy")) { alert("Failed!"); };
};

$(".btn-copy-excel").click(function(){
    $(this).parent().siblings(".copyable").children("textarea").copyText();
});
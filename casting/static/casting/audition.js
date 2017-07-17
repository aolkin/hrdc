$(document.body).on("click", ".btn-copy-excel", function(){
    var el = $(this).parent().siblings(".copyable");
    el.removeAttr("hidden");
    var target = el.children("textarea")[0];
    target.focus();
    target.setSelectionRange(0, target.value.length);
    if (!document.execCommand("copy")) {
        alert("Failed to copy automatically!");
    }
    el.attr("hidden", true);
});
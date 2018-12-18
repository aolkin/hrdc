$(function(){
    function redirect(pos) {
        $form = $("form.geolocation-form");
        $form.children("input").each(function(index, el) {
            let val = pos.coords[$(el).attr("name")];
            if (val) {
                $(el).val(val);
            }
        });
        $form.submit();
    }

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(redirect);
    } else {
        $(".lead").hide();
        $(".alert-danger").show();
    }
});
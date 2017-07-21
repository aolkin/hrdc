$(document.body).on("focus", "input[type=number]", function(e){
    $(this).parent().removeClass("has-danger");
    $(this).siblings(".form-control-feedback").remove();
    $(this).data("number-original-val", $(this).val());
});

$(document.body).on("blur", "input[type=number]", function(e){
    let val = Number($(this).val());
    if (val > Number($(this).attr("max")) ||
	val < Number($(this).attr("min"))) {
	$(this).val($(this).data("number-original-val"));
	$(this).parent().addClass("has-danger");
	$(this).after($("<div>").addClass("form-control-feedback")
		      .text("Invalid number entered."));
    }
});

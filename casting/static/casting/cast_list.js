$(document.body).on("focus", "input[type=number]", function (e) {
    $(this).parent().removeClass("has-danger");
    $(this).siblings(".form-control-feedback").remove();
    $(this).data("number-original-val", $(this).val());
});

$(document.body).on("blur", "input[type=number]", function (e) {
    let val = Number($(this).val());
    if (val > Number($(this).attr("max")) ||
	val < Number($(this).attr("min"))) {
	$(this).val($(this).data("number-original-val"));
	$(this).parent().addClass("has-danger");
	$(this).after($("<div>").addClass("form-control-feedback")
		      .text("Invalid number entered."));
    }
});

function adjustOrder(adjustment, e) {
    let order = $(e.currentTarget).parent().siblings("[data-field=order]");
    order.val(Number(order.val()) + adjustment);
    sendBoundUpdate.apply(order.get(0));
}

$(document.body).on("click", ".btn-decrease", adjustOrder.bind(null, -1));
$(document.body).on("click", ".btn-increase", adjustOrder.bind(null, 1));

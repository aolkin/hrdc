$(() => {
    $("#div_id_venue-venues .form-check-input").each((index, el) => {
	$(el).data("initial", el.checked);
    }).change(function (e) {
	$(".venue-removal-warning").hide();
	$("#div_id_venue-venues .form-check-input").each((index, el) => {
	    if ($(el).data("initial") && !el.checked) {
		$(".venue-removal-warning").show();
	    }
	})
    });
    $(".venue-removal-warning").hide();
});

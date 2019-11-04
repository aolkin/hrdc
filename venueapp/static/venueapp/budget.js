$(() => {
    function deleteLine() {
	let fieldset = $(this).parents(".budget-line");
	fieldset.find(".form-check-input").prop("checked", true);
	fieldset.addClass("pending-delete");
	$(this).fadeOut();
    }
    $(".budget-line").on("click", ".remove-line", deleteLine);

    let formatter = new Intl.NumberFormat('en-US', {
	style: 'currency',
	currency: 'USD',
    });

    function recalculate() {
	let net = 0;
	$(".budget-line .dollar-field input").each((index, el) => {
	    let multiplier = $(el).parents(".dollar-field").hasClass(
		"category-income") ? 1 : -1;
	    net += $(el).val() * multiplier;
	});
	$("#net-total").val(formatter.format(net));
    }

    $(".dollar-field input").each((index, el) => {
	let $el = $(el);
	let prepend = $("<div>").addClass("input-group-prepend");
	prepend.append('<span class="input-group-text">$</span>');
	$el.parent().addClass("input-group");
	$el.parent().prepend(prepend);
	$el.addClass("text-right");
    }).on("input", recalculate);
    recalculate();

    $('a[data-toggle="tab"]').on('shown.bs.tab', function (e) {
	$(".add-budget-venue input").val($(this).data("venue"));
    }).eq(0).trigger("shown.bs.tab");
});

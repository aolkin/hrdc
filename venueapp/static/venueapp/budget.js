$(() => {
    function deleteLine() {
	let fieldset = $(this).parents(".budget-line");
	fieldset.find(".form-check-input").prop("checked", true);
	fieldset.addClass("pending-delete");
	$(this).fadeOut();
    }
    $(".budget-line").on("click", ".remove-line", deleteLine);

    $(".dollar-field input").each((index, el) => {
	let $el = $(el);
	let prepend = $("<div>").addClass("input-group-prepend");
	prepend.append('<span class="input-group-text">$</span>');
	$el.parent().addClass("input-group");
	$el.parent().prepend(prepend);
    });

    $('a[data-toggle="tab"]').on('shown.bs.tab', function (e) {
	$(".add-budget-venue input").val($(this).data("venue"));
    }).eq(0).trigger("shown.bs.tab");
});

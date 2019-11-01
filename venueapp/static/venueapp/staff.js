$(() => {
    function select_other(e) {
	if ($(this).find(":selected").parent().attr("label") == "Other") {
	    let fieldset = $(this).parents(".staff-form");
	    fieldset.find(".other-field label").text(
		fieldset.find("select :selected").text());
	    fieldset.find(".role-field").hide();
	    fieldset.find(".other-field").show();
	}
    }

    $(".role-field select.select").select2().change(select_other).each(
	(i, el) => {
	    select_other.apply(el);
	}
    );

    function deleteStaff() {
	let fieldset = $(this).parents(".staff-form");
	fieldset.find(".form-check-input").prop("checked", true);
	fieldset.addClass("pending-delete");
	$(this).fadeOut();
    }
    $(".staff-form").on("click", ".remove-person", deleteStaff);
});

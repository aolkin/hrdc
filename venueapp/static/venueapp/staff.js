$(() => {
    $(".role-field select.select").select2().change(function(e) {
	console.log(this);
    });


    function deleteIncome() {
	let fieldset = $(this).parents(".staff-form");
	fieldset.find(".form-check-input").prop("checked", true);
	fieldset.addClass("pending-delete");
	$(this).fadeOut();
    }
    
    $(".staff-form").on("click", ".remove-person", deleteIncome);

});

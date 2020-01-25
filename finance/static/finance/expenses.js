
$(() => {
    function deleteExpense() {
	let fieldset = $(this).parents(".expense-form");
	fieldset.find(".delete-field .form-check-input").prop("checked", true);
	fieldset.slideUp();
    }
    
    $(".expenseform").on("click", ".remove-expense", deleteExpense);

    $(".dollar-field input").each((index, el) => {
	let $el = $(el);
	let prepend = $("<div>").addClass("input-group-prepend");
	prepend.append('<span class="input-group-text">$</span>');
	$el.parent().addClass("input-group");
	$el.parent().prepend(prepend);
    });

    $(".purchased-using select").change(function() {
	let fieldset = $(this).parents(".expense-form");
	fieldset.find(".reimbursement-options").toggleClass(
	    "d-none", $(this).val() != 1);
    }).change();

    $(".reimburse-via select").change(function() {
	let fieldset = $(this).parents(".expense-form");
	fieldset.find(".mailing-address").toggleClass(
	    "d-none", $(this).val() != 1);
	fieldset.find(".venmo-handle").toggleClass(
	    "d-none", $(this).val() != 2);
    }).change();

    $("input[type=file]").each((index, el) => {
	$el = $(el);
	let filename = $el.parents(".receipt-field").data("filename");
	$el.parent().addClass("custom-file");
	$el.addClass("custom-file-input");
	$el.parent().append(
	    $("<label>").addClass("custom-file-label").text(
		filename || "Upload a new receipt"));
	$el.change(function() {
	    $(this).parent().children("label").text(this.files[0].name);
	});
    });
});

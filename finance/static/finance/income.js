
$(() => {   
    let extra = $("fieldset").last();
    let count = Number($("#id_income_set-TOTAL_FORMS").val());

    function deleteIncome() {
	let fieldset = $(this).parents(".income-form");
	fieldset.find(".form-check-input").prop("checked", true);
	fieldset.slideUp();
    }
    
    $(".incomeform").on("click", ".remove-income", deleteIncome);

    $("option").each((index, el) => {
	if (Number($(el).val()) > 90) {
	    $(el).attr("disabled", true);
	}
    });

    $(".dollar-field input").each((index, el) => {
	let $el = $(el);
	let prepend = $("<div>").addClass("input-group-prepend");
	prepend.append('<span class="input-group-text">$</span>');
	$el.parent().addClass("input-group");
	$el.parent().prepend(prepend);
    });
    
    let formatter = new Intl.NumberFormat('en-US', {
	style: 'currency',
	currency: 'USD',
    });

    function calculateTotal() {
	let requested = total_confirmed_income;
	let received = total_confirmed_income;
	$(".income-form").each((index, el) => {
	    let form = $(el);
	    if (form.find(".status-field select").val() != 11) {
		var val = Number(form.find(".requested-field input").val());
		if (!isNaN(val)) {
		    requested += val;
		}
		val = Number(form.find(".received-field input").val());
		if (!isNaN(val)) {
		    received += val;
		}
	    }
	});
	$("#total-requested-income").text(formatter.format(requested));
	$("#total-received-income").text(formatter.format(received));
    }
    
    $(".dollar-field input, .status-field select").on("change keypress",
						      calculateTotal);
    calculateTotal();
});

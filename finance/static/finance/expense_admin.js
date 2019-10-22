django.jQuery(() => {
    let $ = django.jQuery;

    $("#id_show").on("change input", function(e) {
	$.ajaxSetup({
	    headers: {
		"X-Expense-Subcategory-Show": $(this).val() || "",
	    },
	});
    }).change();
});

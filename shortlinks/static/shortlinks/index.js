$(() => {
    $(".url-field input").on("input", function() {
	let res = $($(this).parents(".url-field").data("shortened"));
	res.val(res.data("prefix") + $(this).val());
    });
});

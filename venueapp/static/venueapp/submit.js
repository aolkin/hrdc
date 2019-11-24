$(() => {
    $(".submit-app").click(() => {
	$("#submit-confirm-modal").modal("show");
    });
    $("#submit-confirm-modal input[type=checkbox]").change(function() {
	$("#submit-confirm-modal button[type=submit]").attr(
	    "disabled", !this.checked);
    }).change();
});

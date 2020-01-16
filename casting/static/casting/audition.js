$(document.body).on("click", ".btn-copy-excel", function(){
    var el = $(this).parent().siblings(".copyable");
    el.removeAttr("hidden");
    var target = el.children("textarea")[0];
    target.focus();
    target.setSelectionRange(0, target.value.length);
    if (!document.execCommand("copy")) {
        alert("Failed to copy automatically!");
    }
    el.attr("hidden", true);
});

$(document.body).on("click", ".call-btn", function() {
    $("#fetch-actor-name").text($(this).data("actor-name"));
    $("#fetch-msg-modal").modal("show");
});


function hideFilteringMessage(always) {
    if (always === true) {
        localStorage.hideStatusFilteringMessage = true;
    }
    $(".filterable-instructions").popover("hide");
}

$(function() {
    $("th.status-header a").click(function(e){
	e.stopPropagation();
	let marker = $(this).data("marker");
	let state = $(this).toggleClass("text-dark").hasClass("text-dark");
	$("table tbody tr td:nth-child(6)").each(
	    function(index, el) {
		if ($(el).text().includes(marker)) {
		    $(el).parent().toggleClass("d-none", state);
		}
	    }
	);
    });

    if (localStorage.hideStatusFilteringMessage != "true") {
        $(".filterable-instructions").popover({
	    sanitize: false
	});
        $(".filterable-instructions").popover("show");
        $(".filterable-instructions-dismiss").click(hideFilteringMessage);
    }
});

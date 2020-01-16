
function filterTable(column, val) {
    $("table tbody tr td:nth-child(" + column + ")").each(
	function(index, el) {
	    if (!$(el).text().toLowerCase().includes(val.toLowerCase())) {
		$(el).parent().addClass("d-none");
	    } else {
		$(el).parent().removeClass("d-none");
	    }
	}
    );
}

function hideFilteringMessage(always) {
    if (always === true) {
        localStorage.hideFilteringMessage = true;
    }
    $(".filterable-instructions").popover("hide");
}

$(function() {

    $("th.filterable").click(function(e){
        if (!$(this).children("span").hasClass("d-none")) {
	    $(this).children("span").addClass("d-none");
	    $(this).children("input").removeClass("d-none").focus();
	}
	e.stopPropagation();
    });
    $("html").on("click", function(e) {
	$("th.filterable").each(function(index, el) {
	    if ($(el).children("input").val() != "") {
		$(el).children("input").val("").keyup();
	    }
	    $(el).children("input").addClass("d-none");
	    $(el).children("span").removeClass("d-none");
	});
    });
    $("th.filterable input").keyup(function(e) {
	filterTable($(this).data("n"), $(this).val());
    });

    $("#chat-window").click(function(e) {
        e.stopPropagation();
    });

    if (localStorage.hideFilteringMessage != "true") {
        $(".filterable-instructions").popover({
	    sanitize: false
	});
        $(".filterable-instructions").popover("show");
        $(".filterable-instructions-dismiss").click(hideFilteringMessage);
    }

});

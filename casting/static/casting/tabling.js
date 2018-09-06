
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

$(function() {

    $("th.filterable").click(function(e){
        if (!$(this).children("span").hasClass("d-none")) {
	    $(this).children("span").addClass("d-none");
	    $(this).children("input").removeClass("d-none");
	}
	e.stopPropagation();
    });
    $(document.body).on("click", function(e) {
	console.log("document clicked");
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
    
});

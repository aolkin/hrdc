
$(() => {   
    let DATE_FORMAT = "YYYY-MM-DD";

    $(".dateinput").each((index, el) => {
	let $el = $(el);
	$el.attr("autocomplete", "off");
	$el.data("toggle", "datetimepicker");
	$el.data("target", "#" + $el.attr("id"));
	$el.addClass("datetimepicker-input");
	$el.datetimepicker({
	    format: DATE_FORMAT,
	    useCurrent: false,
	    date: moment($el.val(), DATE_FORMAT),
	    minDate: moment().subtract(1, "days"),
	});
    }).on("focus", function () {
	$(this).datetimepicker("show");
    }).on("blur", function () {
	$(this).datetimepicker("hide");
    });

    $(".calendar-select input, .calendar-select select").change(function() {
	let year = $(".calendar-select input").val();
	let month = $(".calendar-select select").val();
	let embed = new URLSearchParams(location.search).get("embed");
	console.log(embed);
	location.assign($(".calendar-select").data("url") +
			year + "/" + month + "/" + (embed?"?embed="+embed:""));
    });

    $('[data-toggle="tooltip"]').tooltip()
});

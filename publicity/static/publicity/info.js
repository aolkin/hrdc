
$(() => {   
    let DATETIME_FORMAT = "dddd, MMMM D, Y [at] h:mm A"

    let extra = $("fieldset").last();
    let count = Number($("#id_performancedate_set-TOTAL_FORMS").val());
    if (!extra.find(`#id_performancedate_set-${count - 1}-performance`).val()) {
	extra.hide();
    }

    function addPerformance() {
	let newPerformance = extra.clone();
	newPerformance.show();
	newPerformance.find(`#id_performancedate_set-${count - 1}-id`).attr(
	    "name", `performancedate_set-${count}-id`);
	newPerformance.find(`#id_performancedate_set-${count - 1}-DELETE`).attr(
	    "name", `performancedate_set-${count}-DELETE`);
	newPerformance.find(`#id_performancedate_set-${count - 1}-show`).attr(
	    "name", `performancedate_set-${count}-show`);
	newPerformance.find(`#id_performancedate_set-${count - 1}-performance`).attr(
	    "name", `performancedate_set-${count}-performance`);
	newPerformance.data("id", count);
	$(".performancedate_formset").append(newPerformance);
	count += 1;
	$("#id_performancedate_set-TOTAL_FORMS").val(count);
    }

    $(".add-performance").click(addPerformance);

    function deletePerformance() {
	let fieldset = $(this).parent();
	let id = fieldset.data("id");
	console.log(id);
	if (fieldset.find(`#id_performancedate_set-${id}-id`).val()) {
	    fieldset.find(".form-check-input").prop("checked", true);
	}
	fieldset.slideUp();
    }
    
    $(".performancedate_formset").on(
	"click", ".delete-performance", deletePerformance);

    $(".performancedate_formset .datetimeinput").each((index, el) => {
	let $el = $(el);
	$el.attr("autocomplete", "off");
	$el.data("toggle", "datetimepicker");
	$el.data("target", "#" + $el.attr("id"));
	$el.addClass("datetimepicker-input");
	$el.datetimepicker({
	    format: DATETIME_FORMAT,
	    useCurrent: false,
	    date: moment($el.val(), DATETIME_FORMAT)
	});
    });
    
    $(".performancedate_formset").on("focus", ".datetimeinput", function () {
	$(this).datetimepicker({
	    format: DATETIME_FORMAT,
	    useCurrent: false,
	    date: moment($(this).val(), DATETIME_FORMAT)
	});
	$(this).datetimepicker("show");
    });

    $(".performancedate_formset").on("blur", ".datetimeinput", function () {
	$(this).datetimepicker("hide");
    });
});

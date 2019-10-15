
$(() => {   
    let DATETIME_FORMAT = "dddd, MMMM D, Y [at] h:mm A"

    let extra = $(".date-fieldset").last();
    let count = Number($("#id_performancedate_set-TOTAL_FORMS").val());
    let initial = count - 1;
    if (!extra.find(`#id_performancedate_set-${initial}-performance`).val()) {
	extra.hide();
    }
    $("input[name$=-note]").attr("placeholder",
				'Note, e.g. "Free with HUID"');

    function addPerformance() {
	let newPerformance = extra.clone();
	newPerformance.show();
	newPerformance.find(`#id_performancedate_set-${initial}-id`).attr(
	    "name", `performancedate_set-${count}-id`);
	newPerformance.find(`#id_performancedate_set-${initial}-DELETE`).attr(
	    "name", `performancedate_set-${count}-DELETE`);
	newPerformance.find(`#id_performancedate_set-${initial}-show`).attr(
	    "name", `performancedate_set-${count}-show`);
	newPerformance.find(`#id_performancedate_set-${initial}-performance`).attr(
	    "name", `performancedate_set-${count}-performance`);
	newPerformance.find(`#id_performancedate_set-${initial}-note`).attr(
	    "name", `performancedate_set-${count}-note`);
	$(".performancedate_formset").append(newPerformance);
	count += 1;
	$("#id_performancedate_set-TOTAL_FORMS").val(count);
    }

    $(".add-performance").click(addPerformance);

    function deletePerformance() {
	let fieldset = $(this).parents(".date-fieldset");
	if (fieldset.find("input[name$=-id]").val()) {
	    fieldset.find("input[name$=-DELETE]").prop("checked", true);
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
	    sideBySide: true,
	    date: moment($el.val(), DATETIME_FORMAT)
	});
    });
    
    $(".performancedate_formset").on("focus", ".datetimeinput", function () {
	$(this).datetimepicker({
	    format: DATETIME_FORMAT,
	    useCurrent: false,
	    sideBySide: true,
	    date: moment($(this).val(), DATETIME_FORMAT)
	});
	$(this).datetimepicker("show");
    });

    $(".performancedate_formset").on("blur", ".datetimeinput", function () {
	$(this).datetimepicker("hide");
    });
});

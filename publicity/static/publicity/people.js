
$(() => {   
    let extra = $("fieldset").last();
    let count = Number($("#id_showperson_set-TOTAL_FORMS").val());

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

    function deletePerson() {
	let fieldset = $(this).parents(".person-form");
	fieldset.find(".form-check-input").prop("checked", true);
	fieldset.slideUp();
    }
    
    $(".peopleform").on("click", ".remove-person", deletePerson);
});

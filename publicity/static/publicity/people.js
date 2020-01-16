$(() => {   
    function deletePerson() {
	let fieldset = $(this).parents(".person-form");
	fieldset.find(".form-check-input").prop("checked", true);
	fieldset.addClass("deleted-row");
    }
    $(".peopleform").on("click", ".remove-person", deletePerson);

    let editing = null;
    let previous = null;
    $("#add-modal").modal({
	"show": false,
	"backdrop": "static",
	"keyboard": false,
    }).on("hide.bs.modal", () => {
	if (editing) {
	    $(editing).val(null).trigger("change");
	    editing = null;
	}
    }).on("show.bs.modal", () => {
	$("#add-modal input[id]").val("").removeClass("is-valid is-invalid");
	$("#add-modal input[type=checkbox]").prop("checked", false);
	$("#add-button").prop("disabled", false);
	$("#add-error").text("");
	$("#add-errors").empty();
    });

    $("#add-button").click(() => {
	let data = {};
	let isValid = true;
	$("#add-modal input[name]").each((index, el) => {
	    $(el).removeClass("is-valid is-invalid");
	    if ($(el).prop("type") == "checkbox") {
		if ($(el).prop("checked")) {
		    data[$(el).prop("name")] = "on";
		}
	    } else {
		data[$(el).prop("name")] = $(el).val();
	    }
	    if ($(el).val()) {
		$(el).addClass("is-valid");
	    } else if ($(el).prop("required")) {
		$(el).addClass("is-invalid");
		isValid = false;
	    }
	});
	if (!isValid) {
	    return false;
	}
	$("#add-button").prop("disabled", true);
	$.post("/people/add/", data).done((data, status, xhr) => {
	    if (data.errors) {
		$("#add-errors").empty();
		for (var field in data.errors) {
		    for (var i = 0; i < data.errors[field].length; i++) {
			$("<li>").text(data.errors[field][i])
				 .appendTo("#add-errors");
		    }
		}
		$("#add-error").text("Unable to Add Person");
	    } else {
		$(editing).append(new Option(data.text, data.id, false, false));
		$(editing).val(data.id).trigger("change");
		editing = null;
		$("#add-modal").modal("hide");
	    }
	}).fail((xhr, status, error) => {
	    $("#add-error").text(error);
	}).always(() => {
	    $("#add-button").prop("disabled", false);
	});
    });

    $(".person-field").select2({
	placeholder: "Search by name, email, or phone...",
        ajax: {
            url: "/people/search/",
            delay: 250,
            processResults(data, params) {
		if (!data || data.length) {
		    return {
                        results: data
		    };
		} else {
		    return {
			results: [{
			    "text": "Add a new person...",
			    "id": 0
			}]
		    };
		}
            },
            minimumInputLength: 3,
            cache: true,
        }
    }).change(function() {
	if ($(this).val() === "0") {
	    editing = this;
	    $("#add-modal").modal("show");
	}
    });
});

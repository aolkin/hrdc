"use strict";

$(() => {
    
    function initialize_select2() {
	$("#id_staff").select2({
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
	}).change(() => {
	    $(".modal-body .bt-messages").slideUp();
	});
    }

    $("#edit-show-modal").on("show.bs.modal", function (event) {
	var button = $(event.relatedTarget);
	var target = button.attr("href");
	$("#edit-show-modal").data("dirty", false);
	if (target) {
            var modal = $(this).find(".modal-body");
            modal.load(target, (response, status, xhr) => {
		initialize_select2();
	    });
	    $("#edit-show-modal-title").text(button.attr("title"));
	}
    }).on("hide.bs.modal", function (event) {
	if ($("#edit-show-modal").data("dirty")) {
	    location.reload();
	}
    });

    $("#edit-show-modal .body-submit").click(function() {
	var modal = $(this).closest(".modal-content");
	var form = modal.find("form");
	$.post(form.attr("action"), form.serialize())
	 .always((data, status, xhr) => {
	     modal.find(".modal-body").html(data);
	     initialize_select2();
	     $("#edit-show-modal").data("dirty", true);
	 });
    });

});

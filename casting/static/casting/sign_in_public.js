$(function(){
    function redirect(pos) {
	if (window.gtag) {
	    gtag('event', "location_found", {
		'event_category': "casting",
		'event_label': "Location Found"
	    });
	}
        $form = $("form.geolocation-form");
        $form.children("input").each(function(index, el) {
            let val = pos.coords[$(el).attr("name")];
            if (val) {
                $(el).val(val);
            }
        });
        $form.submit();
    }

    function noLocation(error) {
	$("p.intro").hide();
        let el = $(".alert-danger").removeClass("d-none");
	switch(error.code) {
	    case error.PERMISSION_DENIED:
		el.text("Location access denied. Please allow access and try again, or sign in at the table.")
		break;
	    case error.TIMEOUT:
		el.find(".message").text("Attempting to determine your location took too long.");
		break;
	}
	if (window.gtag) {
	    let CODES = {};
	    CODES[error.PERMISSION_DENIED] = "PERMISSION_DENIED";
	    CODES[error.TIMEOUT] = "TIMEOUT";
	    CODES[error.POSITION_UNAVAILABLE] = "POSITION_UNAVAILABLE";
	    gtag('event', "location_error", {
		'event_category': "casting",
		'event_label': "Location Error",
		'value': CODES[error.code],
	    });
	}
    }

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(redirect, noLocation, {
	    timeout: 5000,
	});
    } else {
        $("p.intro").hide();
        $(".alert-danger").removeClass("d-none");
    }
});

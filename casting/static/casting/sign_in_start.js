if (window.gtag) {
    $(() => {
	$("form").on("submit", () => {
	    let count = 0;
	    $("input[type=checkbox]").each((index, el) => {
		if (el.checked) {
		    count++;
		}
	    });
	    gtag('event', "sign_in_start", {
		'event_category': "casting",
		'event_label': "Sign In Start",
		'event_value': count,
	    });
	});
    });
}

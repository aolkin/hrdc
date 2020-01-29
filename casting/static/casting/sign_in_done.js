if (window.gtag) {
    $(() => {
	let count = 0;
	$("input[type=checkbox]").each((index, el) => {
	    if (el.checked) {
		count++;
	    }
	});
	gtag('event', "sign_in_done", {
	    'event_category': "casting",
	    'event_label': "Sign In Done",
	    'event_value': count,
	});
    });
}

var suggested_domains;

function suggestEmailDomains(q, cb) {
    let parts = q.split("@");
    if (parts[0] && parts.length === 2 && parts[1]) {
        let matches = [];
	function doCB() {
	    for (let domain of suggested_domains) {
		if (domain.startsWith(parts[1])) {
                    matches.push(parts[0] + "@" + domain);
		}
            }
            cb(matches);
	}
        if (suggested_domains) {
	    doCB();
	} else {
	    $.getJSON("/autocomplete/",
		      { "key": "email_domain"}).done(function(data) {
			  suggested_domains = data;
			  doCB();
		      });
	}
    } else {
        return [];
    }
}

$("input[type=email], input[name=email]").typeahead({
    minLength: 2,
    source: suggestEmailDomains,
    fitToElement: true,
    autoSelect: true
});

function suggestAffiliation(q, cb) {
    $.getJSON("/autocomplete/",
              { "key": "affiliation", "q": q }).done(cb);
}

$("input[name=affiliation]").typeahead({
    minLength: 0,
    source: suggestAffiliation,
    fitToElement: true,
    autoSelect: true,
    showHintOnFocus: true,
});

function updateDisplayName() {
    let name = $("[name=first_name]").val();
    name += " " + $("[name=last_name]").val();
    let year = $("[name=year]").val().toString();
    let affiliation = $("[name=affiliation]").val();
    if (!$("[name=display_affiliation]").prop("checked")) {
	affiliation = "";
	    }
    if (year.length == 4) {
	year = "'" + year.slice(-2);
    }
    if (year) {
	year = " " + year;
    }
    if (affiliation) {
	name += ` (${affiliation}${year})`;
    } else {
	if (year.search("'") > -1) {
	    name += year;
	}
    }
    $("#display_name_field").val(name);
}

$(() => {
    if ($("#display_name_field").length) {
	$("[name=first_name], [name=last_name], [name=affiliation], [name=year], [name=display_affiliation]").on("input", updateDisplayName); 
    }
    updateDisplayName();
});

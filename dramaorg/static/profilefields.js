var SUGGESTED_DOMAINS = [];

$.getJSON("/autocomplete/",
          { "key": "email_domain"}).done(function(data) {
    SUGGESTED_DOMAINS = data;
});

function suggestEmailDomains(q, cb) {
    let parts = q.split("@");
    if (parts[0] && parts.length === 2 && parts[1]) {
        let matches = [];
        for (let domain of SUGGESTED_DOMAINS) {
            if (domain.startsWith(parts[1])) {
                matches.push(parts[0] + "@" + domain);
            }
        }
        cb(matches);
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
    autoSelect: true
});

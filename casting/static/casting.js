"use strict";

$(".edit-show-modal").on("show.bs.modal", function (event) {
    var button = $(event.relatedTarget);
    var target = button.attr("href");
    if (target) {
        var modal = $(this).find(".modal-body");
        modal.load(target);
    }
});

$(".modal .body-submit").click(function() {
    var form = $(this).closest(".modal-content").find("form");
    form.submit();
});

$("a[target=_popout]").click(function(e) {
    e.preventDefault();
    window.open($(this).attr("href") + "popout/",
                "popout", "width=800,height=600");
});

let SUGGESTED_DOMAINS = [
    "college.harvard.edu",
    "gmail.com",
];

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

$("input[type=email]").typeahead({
    minLength: 2,
    source: suggestEmailDomains,
    fitToElement: true,
    autoSelect: true
});

$("a[href][data-autoreset]").each(function(index, el) {
    setTimeout((function(){
        location.assign($(this).attr("href"));
    }).bind(this), $(el).data("autoreset"));
});
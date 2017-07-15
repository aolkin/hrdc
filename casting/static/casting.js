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

function initTooltips(parent) {
    if (!parent) {
        parent = $(document.body);
    }
    parent.find('[data-toggle="tooltip"]').tooltip();
}

$(function() {
    if (window.channels) {
        const bridge = new channels.WebSocketBridge();
        bridge.connect(location.pathname + "ws/");
        bridge.listen(function(data, stream) {
            var el = $("#" + data.id);
            if (el.length < 1) {
                el = $(data.element).attr("id", data.id);
                $(data.container).append(el);
            }
            el.html(data.html);
            if (data.pulse) {
                el.addClass(data.pulse);
                setTimeout(function() {
                    el.addClass("pulse");
                    setTimeout(function() {
                        el.removeClass(data.pulse);
                        setTimeout((function(){
                                        this.removeClass("pulse");
                                    }).bind(el), 1000);
                    }, 0);
                }, 0);
            }
            initTooltips(el);
        });
    }

    initTooltips();
});

$(document.body).on("click", "a.ajaxify", function(e){
    e.preventDefault();
    $.get($(this).attr("href"));
});
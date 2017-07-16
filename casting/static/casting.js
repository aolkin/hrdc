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

function getPK() {
    return Number(location.pathname.split("/").slice(-2, -1)[0]);
}

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

function updateBoundData(action, stream) {
    if (action.action === "update") {
        let els = $("[data-stream=" + stream +
                    "][data-pk=" + action.pk + "]");
        for (let field in action.data) {
            els.filter("[data-field=" + field + "]").val(
                action.data[field]);
        }
    } else if (action.action === "create") {
        let blank = $("#" + stream + "-blank");
        if (blank.length) {
            let el = blank.clone().insertBefore(blank);
            el.removeAttr("id").removeAttr("hidden")
              .removeClass("blank-card").attr("data-pk", action.pk);
            el.find(".card-action").toggleClass("hidden");
            el.find("[data-pk]").attr("data-pk", action.pk);
            for (let field in action.data) {
                el.find("[data-field=" + field + "]").val(
                    action.data[field]);
            }
            $(".card-deck").scrollTo(el, 500, {
                interrupt: true,
            });
            initTooltips(el);
        } else {
            console.log("Attempted to create " + stream +
                        "; missing blank.");
        }
    } else if (action.action === "delete") {
        let el = $("div.card[data-pk=" + action.pk + "]").remove();
    }
}
function sendBoundUpdate(e) {
    let fields = {};
    fields[$(this).data("field")] = $(this).val().replace(/\s*$/,"");
    bridge.stream($(this).data("stream")).send({
        action: "update",
        pk: $(this).data("pk"),
        data: fields,
    });
}

var bridge;

$(function() {
    if (window.channels) {
        bridge = new channels.WebSocketBridge();
        bridge.connect(location.pathname + "ws/");
        bridge.listen(function(data, stream) {
            console.log(data, stream);
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
        const STREAMS = ["castingmeta", "character"];
        for (let stream of STREAMS) {
            bridge.demultiplex(stream, updateBoundData);
        }
        let delay = (function(){
                         let timer = 0;
                         return function(callback, ms){
                             clearTimeout (timer);
                             timer = setTimeout(callback, ms);
                         };
                     })();
        $(document.body).on("blur", "[data-stream][data-pk][data-field]",
                            sendBoundUpdate);
        $(document.body).on("keyup", "[data-stream][data-pk][data-field]",
                            function (e) {
                                delay(sendBoundUpdate.bind(this), 500);
                            });
        $(document.body).on("click", ".card-action.btn-success", function(e) {
            bridge.stream($(this).data("stream")).send({
                action: "create",
                data: { "show": getPK() },
            });
        });
        $(document.body).on("click", ".card-action.btn-danger", function(e) {
            bridge.stream($(this).data("stream")).send({
                action: "delete",
                pk: $(this).data("pk"),
            });
        });
    }

    initTooltips();
});

$(document.body).on("click", "a.ajaxify", function(e){
    e.preventDefault();
    $.get($(this).attr("href"));
});
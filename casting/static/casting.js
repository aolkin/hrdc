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
    "hrdctheater.com",
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

function initSelects(parent) {
    if (!parent) {
	parent = $("li.stream-item:not(.blank)");
    }
    parent.find("[data-select-src]").each(function(index, el) {
        $(this).select2({
            placeholder: $(this).data("select-placeholder"),
            ajax: {
                url: $(this).data("select-src"),
                delay: 250,
                processResults(data, params) {
                    return {
                        results: data
                    };
                },
                minimumInputLength: 1,
                cache: true,
            }
        });
    });
}

class DataBindingHandler {
    constructor(stream) {
        this.stream = stream;
	this.updateBoundData = this.updateBoundData.bind(this);
    }

    updateBoundData(action, stream) {
	if (!this.stream || stream === this.stream) {
	    let f = this["do_" + action.action];
	    if (f) {
		f(action, stream);
	    }
	}
    }

    do_update(action, stream) {
        let els = $("[data-stream=" + stream +
                    "][data-pk=" + action.pk + "]");
        for (let field in action.data) {
            let el = els.filter("[data-field=" + field + "]");
            if (el.is("select")) {
                $.get("actor/" + action.data[field],
                      (function(data) {
                          $("<option>").text(data.text).attr("value", data.id)
                                       .appendTo(this);
                          this.val(data.id);
                          this.trigger("change");
                      }).bind(el));
            } else {
                el.val(action.data[field]);
            }
        }
    }
    do_create(action, stream) {
	let parent = (action.data.character ?
		      $("[data-stream=character][data-pk=" +
			action.data.character + "]") :
		      $(document.body));
        let blank = parent.find("." + stream + "-blank");
        if (blank.length) {
            let el = blank.clone().insertBefore(blank);
            el.removeClass(stream + "-blank").removeClass("blank")
		.attr("data-pk", action.pk);
            el.find(".btn-action[data-stream=" + stream +
                    "]").toggleClass("hidden");
            el.find("[data-pk][data-stream=" + stream +
                    "]").attr("data-pk", action.pk);
            if (action.model === "casting.character") {
                el.find("[data-character]").data("character", action.pk);
            }
            for (let field in action.data) {
                el.find("[data-field=" + field + "][data-stream=" + stream +
                        "]").val(
                    action.data[field]);
            }
	    if (el.hasClass("scroll-after-create")) {
		$(".card-deck").scrollTo(el, 500, {
                    interrupt: true,
		});
	    }
	    initTooltips(el);
            if (action.data.character) {
		initSelects(el);
            }
        } else {
            throw "Cannot create " + stream + " without blank.";
        }
    }
    do_delete(action, stream) {
        let el = $(".stream-item[data-pk=" + action.pk + "][data-stream=" +
		   stream + "]").remove();
    }
}

function sendBoundUpdate(e) {
    if ($(this).data("pk")) {
        let fields = {};
        let value = $(this).val();
        fields[$(this).data("field")] = value;
        bridge.stream($(this).data("stream")).send({
            action: "update",
            pk: $(this).data("pk"),
            data: fields,
        });
    }
}

var bridge;

$(function() {
    if (window.channels) {
        bridge = new channels.WebSocketBridge();
        bridge.connect(location.pathname + "ws/");
        bridge.listen(function(data, stream) {
            var el = $("#" + data.id);
            if (el.length < 1) {
                el = $(data.element).attr("id", data.id);
                $(data.container).append(el);

		$(window).scrollTo(el, 500, {
                    interrupt: true,
		});
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
        const STREAMS = ["castingmeta", "character", "callback"];
	const binder = new DataBindingHandler();
        for (let stream of STREAMS) {
            bridge.demultiplex(stream, binder.updateBoundData);
        }
        let delay = (function() {
            let timer = 0;
            return function(callback, ms) {
                clearTimeout (timer);
                timer = setTimeout(callback, ms);
            };
        }());
        $(document.body).on("blur select2:select",
			    "[data-stream][data-pk][data-field]",
                            sendBoundUpdate);
        $(document.body).on("keyup", "[data-stream][data-pk][data-field]",
                            function (e) {
                                delay(sendBoundUpdate.bind(this), 500);
                            });
        $(document.body).on("click", ".btn-create", function(e) {
	    let extra = { };
	    if ($(this).data("extras")) {
		for (let efield of $(this).data("extras").split(",")) {
		    extra[efield] = $(this).data(efield);
		}
	    }
            bridge.stream($(this).data("stream")).send({
                action: "create",
                data: extra,
            });
        });
        $(document.body).on("click", ".btn-delete", function(e) {
            bridge.stream($(this).data("stream")).send({
                action: "delete",
                pk: $(this).data("pk"),
            });
        });
    }

    initTooltips();
    initSelects();
});

$(document.body).on("click", "a.ajaxify", function(e){
    e.preventDefault();
    $.get($(this).attr("href"));
});

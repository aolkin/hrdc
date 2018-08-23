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

function getPK() {
    return Number(location.pathname.split("/").slice(-2, -1)[0]);
}

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
    parent.find('[data-toggle="popover"]').popover();
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
        if (action.data.hidden_for_signing) {
            els.remove();
        }
        for (let field in action.data) {
            let el = els.filter("[data-field=" + field + "]");
            if (el.is("select")) {
		if (action.data[field]) {
                    $.get("actor/" + action.data[field],
			  (function(data) {
                              $("<option>").text(data.text)
				  .attr("value", data.id).appendTo(this);
                              this.val(data.id);
                              this.trigger("change");
			  }).bind(el));
		} else {
		    el.val(null);
		    el.trigger("change");
		}
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
	    let createbtn = el.find(".btn-action.btn-create[data-stream=" +
				    stream + "]");
	    if (createbtn.parent().is(".input-group-append") &&
		!createbtn.siblings().is("button")) {
		createbtn.parent().remove();
	    } else {
		createbtn.remove();
	    }
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

function notifyDisconnect() {
    $(document.body).append(
	'<nav class="navbar fixed-top navbar-danger bg-danger ' +
	    'justify-content-center">' +
	    '<span class="navbar-text text-light">' +
	    'You have disconnected from the server and may miss ' +
	    'some updates. Please <a class="text-white" href="">' +
	    'refresh this page</a>.</span></nav>');
}

var bridge;

$(function() {
    if (window.channels) {
        bridge = new channels.WebSocketBridge();
        bridge.connect(location.pathname + "ws/");

	bridge.socket.addEventListener('close', notifyDisconnect);
        window.addEventListener('offline', notifyDisconnect);

        bridge.listen(function(data, stream) {
            var el = $("#" + data.id);
            if (el.length < 1) {
                el = $(data.element).attr("id", data.id);
                $(data.container).append(el);

                requestAnimationFrame(function() {
                    if (data.scroll) {
		        $(data.scroll).scrollTo("100%", 200);
                    } else {
		        $(window).scrollTo(el, 500, {
                            interrupt: true,
		        });
                    }
                });
            }
            el.html(data.html);
            if (data.pulse) {
                let pulse_el = data.pulse_el ? $(data.pulse_el) : el;
                pulse_el.addClass(data.pulse);
                setTimeout(function() {
                    pulse_el.addClass("pulse");
                    setTimeout(function() {
                        pulse_el.removeClass(data.pulse);
                        setTimeout((function(){
                                        this.removeClass("pulse");
                                    }).bind(pulse_el), 1000);
                    }, 0);
                }, 0);
            }
            initTooltips(el);
        });
        const STREAMS = ["castingmeta", "character", "callback", "signing"];
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
        $(document.body).on("click", ".btn-hide", function(e) {
            console.log("Hide");
            bridge.stream($(this).data("stream")).send({
                action: "update",
                pk: $(this).data("pk"),
                data: {
                    "hidden_for_signing": true,
                },
            });
        });
    }

    initTooltips();
    initSelects();

    $("#chat-entry").keypress(function(e) {
        if (e.which == 13) {
            bridge.send({
                msg: $(this).val()
            });
            $(this).val("");
        }
    });

    $(".scroll-on-load").scrollTo("100%");
    $("#chat-window .fa-window-minimize").click(function(){
        $(".chat-minimizable").slideToggle(200);
    })
});

$(document.body).on("click", "a.ajaxify", function(e){
    e.preventDefault();
    $.get($(this).attr("href"));
});

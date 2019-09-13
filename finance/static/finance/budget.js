function calculateTotals() {
    let formatter = new Intl.NumberFormat('en-US', {
	style: 'currency',
	currency: 'USD',
    });

    let categories = {};
    let totals = {
	estimate: 0,
	reported: 0,
	actual: 0
    };	
    $(".subtotals-category").each((index, el) => {
	let category = $(el).data("category");
	categories[category] = {
	    estimate: 0,
	    reported: 0,
	    actual: 0
	};
	for (let field in categories[category]) {
	    $(".category-" + category + " input[name=" + field + "]").each(
		(i, input) => {
		    let val = Number($(input).val());
		    if (!isNaN(val)) {
			categories[category][field] += val;
		    }
		    if (field == "actual") {
			$(input).parents(".budget-expense-row").find(
			    ".delete-item").toggle(val == 0);
		    }
		}
	    );
	    $(el).find(".total-field-" + field).text(
		formatter.format(categories[category][field]));
	    totals[field] += categories[category][field];
	}
    });
    for (let field in totals) {
	$(".subtotals-all").find(".total-field-" + field).text(
	    formatter.format(-totals[field]));
	$(".subtotals-net").find(".total-field-" + field).text(
	    formatter.format(income_totals[field] - totals[field]));
	$(".subtotals-net").find(".total-field-" + field).toggleClass(
	    "text-danger", income_totals[field] - totals[field] < 0);
    }
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
	    let el = els.filter("[name=" + field + "]");
	    el.val(action.data[field]);
        }
	calculateTotals();
    }

    do_create(action, stream) {
	let category = action.data.category;
        let blank = $("." + stream + "-blank.category-" + category);
        if (blank.length) {
	    let el = blank.clone().insertBefore(blank);
	    el.removeClass(stream + "-blank").removeClass("blank-item")
	      .attr("data-pk", action.pk);
	    el.find("[data-pk][data-stream=" + stream +
		    "]").attr("data-pk", action.pk);
	    for (let field in action.data) {
                el.find("[name=" + field + "][data-stream=" + stream + "]").val(
		    action.data[field]);
	    }
        } else {
	    throw "Cannot create " + stream + " without blank.";
        }
	calculateTotals();
    }

    do_delete(action, stream) {
        let el = $(".stream-item[data-pk=" + action.pk + "][data-stream=" +
		   stream + "]").remove();
	calculateTotals();
    }
}

var bridge;

function sendBoundUpdate(e) {
    if ($(this).data("pk")) {
        let fields = {};
        let value = $(this).val();
        fields[$(this).attr("name")] = value;
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
	'You have disconnected from the server and your changes may not ' +
	'be saved. Please <a class="text-white" href="">' +
	'refresh this page</a>.</span></nav>');
}

$(function() {
    if (window.channels) {
        bridge = new channels.WebSocketBridge();
        bridge.connect(location.pathname + "ws/");
	bridge.listen(()=>console.log("listen", arguments));

	bridge.socket.addEventListener('close', notifyDisconnect);
        window.addEventListener('offline', notifyDisconnect);

        const STREAMS = ["budgetexpense"];
	const binder = new DataBindingHandler();
        for (let stream of STREAMS) {
	    bridge.demultiplex(stream, binder.updateBoundData);
        }
        let debounce = (function() {
	    let timer = 0;
	    return function(callback, ms) {
                clearTimeout (timer);
                timer = setTimeout(callback, ms);
	    };
        }());
        $(document.body).on("change", "[data-stream][data-pk][name]",
			    sendBoundUpdate);
        $(document.body).on("input", "[data-stream][data-pk][name]",
			    function (e) {
                                debounce(sendBoundUpdate.bind(this), 500);
			    });
        $(document.body).on("click", ".add-item", function(e) {
	    bridge.stream($(this).data("stream")).send({
                action: "create",
                data: {
		    category: $(this).data("category"),
		    show: stream_show
		},
	    });
        });
        $(document.body).on("click", ".delete-item", function(e) {
	    bridge.stream($(this).data("stream")).send({
                action: "delete",
                pk: $(this).data("pk"),
	    });
        });
    }

    calculateTotals();
});

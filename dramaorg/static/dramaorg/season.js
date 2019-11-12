
$(() => {   
    let DATE_FORMAT = "YYYY-MM-DD";

    $(".dateinput").each((index, el) => {
	let $el = $(el);
	$el.attr("autocomplete", "off");
	$el.data("toggle", "datetimepicker");
	$el.data("target", "#" + $el.attr("id"));
	$el.addClass("datetimepicker-input");
	$el.datetimepicker({
	    format: DATE_FORMAT,
	    useCurrent: false,
	    date: moment($el.val(), DATE_FORMAT),
	    minDate: moment().subtract(1, "days"),
	});
    }).on("focus", function () {
	$(this).datetimepicker("show");
    }).on("blur", function () {
	$(this).datetimepicker("hide");
    });

    let shows = JSON.parse($("#show-data").text());
    let spaces = JSON.parse($("#space-data").text());
    let venues = {};
    let first = moment().add(10, "years").endOf("year");
    let last = moment(0);
    for (var i = 0; i < shows.length; i++) {
	shows[i].space = spaces[shows[i].space];
	shows[i].start = moment(shows[i].residency_starts);
	shows[i].end = moment(shows[i].residency_ends);

	first = moment.min(shows[i].start, first);
	last = moment.max(shows[i].end, last);

	if (venues[shows[i].space] === undefined) {
	    venues[shows[i].space] = [];
	}
	venues[shows[i].space].push(shows[i]);
    }
    let total_days = last.diff(first, "days");
    console.log(shows, spaces, venues, total_days);

    let HEIGHT = 7;

    Vue.component("show", {
	template: `
	  <div class="season-show-block"
	    :style="{ height: height + 'px', top: top + 'px' }">
	    {{ show.title }}
	  </div>
	`,
	props: ["show"],
	computed: {
	    top() {
		return this.show.start.diff(first, "days") * HEIGHT;
	    },
	    height() {
		return this.show.end.diff(this.show.start, "days") * HEIGHT;
	    }
	}
    });

    let app = new Vue({
	el: "#season-vue",
	data: {
	    "venues": venues,
	    "total_days": total_days,
	},
	computed: {
	    height() {
		return this.total_days * HEIGHT;
	    }
	}
    });
});

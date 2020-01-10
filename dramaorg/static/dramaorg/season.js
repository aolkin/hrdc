
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

    for (var i = 0; i < shows.length; i++) {
	shows[i].space = spaces[shows[i].space];
    }

    let HEIGHT = 7;
    let MIN_DAYS = 4;
    let MIN_HEIGHT = MIN_DAYS + 1;

    Vue.component("show", {
	template: `
	  <div class="season-show-block"
	    :style="{ height: height + 'px', top: top + 'px' }"
	    @click="$emit('select', show)">
	    {{ show.title }}
	  </div>
	`,
	props: ["show", "first", "index"],
	computed: {
	    start() {
		return moment(this.show.residency_starts);
	    },
	    end() {
		return moment(this.show.residency_ends);
	    },
	    top() {
		if (this.start.isValid()) {
		    return this.start.diff(this.first, "days") * HEIGHT;
		}
		return this.index * HEIGHT * MIN_HEIGHT;
	    },
	    height() {
		return Math.max(
		    (this.end.diff(this.start, "days") + 1) * HEIGHT,
		    MIN_DAYS * HEIGHT);
	    }
	}
    });

    let app = new Vue({
	el: "#season-vue",
	data: {
	    "shows": shows,
	    "spaces": spaces,
	    "editing": null,
	},
	computed: {
	    first() {
		let first = moment().add(10, "years").endOf("year");
		for (var i = 0; i < this.shows.length; i++) {
		    let start = moment(this.shows[i].residency_starts);
	    	    if (start.isValid()) {
			first = moment.min(start, first);
		    }
		}
		return first.day(0);
	    },
	    last() {
		let last = moment(0);
		for (var i = 0; i < this.shows.length; i++) {
		    let start = moment(this.shows[i].residency_starts);
		    let end = moment(this.shows[i].residency_ends);
	    	    if (end.isValid()) {
			last = moment.max(end, last);
		    }
	    	    if (start.isValid()) {
			last = moment.max(start.add(MIN_DAYS, "d"), last);
		    }
		}
		return last.day(6).add(7, "d");
	    },
	    total_days() {
		return this.last.diff(this.first, "days");
	    },
	    height() {
		return this.total_days * HEIGHT;
	    },
	    venues() {
		let venues = {};
		for (var i = 0; i < this.shows.length; i++) {
		    if (venues[this.shows[i].space] === undefined) {
			venues[this.shows[i].space] = [];
		    }
		    venues[this.shows[i].space].push(this.shows[i]);
		}
		return venues;
	    },
	    calendar() {
		let weeks = [];
		let date = this.first.clone();
		while (date.isBefore(this.last)) {
		    weeks.push(date.format("MMM D") + " - " +
			       date.add(6, "d").format("MMM D"));
		    date.add(1, "d");
		}
		return weeks;
	    },
	},
	methods: {
	    edit(show) {
		this.editing = show;
		console.log(show);
	    },
	    close() {
		this.editing = null;
	    },
	}
    });
});

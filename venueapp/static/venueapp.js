"use strict";

let cc = {};
cc.dirty = false;

$(function () {
    $(document.body).on("input", "input, select, textarea", function () {
        cc.dirty = true;
    });
    $("[type=submit]").on("click keyup submit", function (e) {
        cc.dirty = false;
    });
    window.onbeforeunload = function () {
        if (cc.dirty) {
            return "Welp!";
        }
    }
});

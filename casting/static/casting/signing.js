"use strict";

let cc = {};
cc.dirty = false;

$(function () {
    $("select").change(function () {
        cc.dirty = true;
    });
    $("[type=submit]").on("click keyup submit", function () {
        cc.dirty = false;
    });
    window.onbeforeunload = function () {
        if (cc.dirty) {
            return "You have not submitted your signing choices!";
        }
    }
});
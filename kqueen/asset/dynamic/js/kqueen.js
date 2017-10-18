/*
 * Common JS definitions
 */
Math.radians = function(degrees) {
    return degrees * Math.PI / 180;
};

// Converts from radians to degrees.
Math.degrees = function(radians) {
    return radians * 180 / Math.PI;
};

$(document).ready(function() {
    if (location.hash) {
        $("a[data-tabcode='" + location.hash + "']").tab("show");
    }
    $(document.body).on("click", "a[data-toggle]", function(event) {
        location.hash = this.getAttribute("data-tabcode");
    });
});
$(window).on("popstate", function() {
    var anchor = location.hash || $("a[data-toggle='tab']").first().attr("href");
    $("a[data-tabcode='" + anchor + "']").tab("show");
});

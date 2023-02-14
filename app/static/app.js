// Stop bubbling for dropdown menu forms
$(".dropdown-menu").click(function (e) {
	e.stopPropagation();
	if ($(e.target).is('[data-toggle=modal]')) {
        $($(e.target).data('target')).modal()
    }
});

// ///////////////////////////////////////////////
// //** Phrasebook Sort */
// $("a#nameSort").bind("click", function() {
//     Cookies.set("sort", "name");
// });
// $("a#langSort").bind("click", function() {
//     Cookies.set("sort", "language");
// });
// $("a#idSort").bind("click", function() {
//     Cookies.set("sort", "id");
// });


///////////////////////////////////////////////
//** Phrasebook Accordion Groups */


$(document).ready(function () {
	let last = Cookies.get("activeAccordionGroup");

	if (last != null) {
		//remove default collapse settings
		// $("#accordion .collapse").removeClass("show");
		//show the last visible group
		$("#" + last).collapse("show");
		// $("#"+last).addClass("show");
	}
});

//when a group is shown, save it as the active accordion group
$("#accordion").bind("shown.bs.collapse hidden.bs.collapse", function () {
    let active = $("#accordion .show").attr("id");
	Cookies.set("activeAccordionGroup", active);

	// if (Cookies.get("activeAccordionGroup") === active) {
	// 	Cookies.remove("activeAccordionGroup");
	// } else {
	// }
});

//Delete accordion position cookie when navigating away from page
let currentPath = window.location.pathname
if (currentPath !== "/user") {
    Cookies.remove("activeAccordionGroup");
}



// let $myGroup = $('#myGroup');
// $myGroup.on('show.bs.collapse','.collapse', function() {
// $myGroup.find('.collapse.show').collapse('hide');
// });

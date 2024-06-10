function show_next_results(btn) {
	let page = btn.text();
	let results = $('.card-small');
	console.log(btn.text());
	
	$('.disabled').toggleClass('disabled')
	$(results).hide();
	$('.active').toggleClass('active')
	$(btn).parent().toggleClass('active')

	let low = (page * 50) - 49;
	let high = (page * 50)
	
	for (let i = low; i <= high; i++) {
		$(results[i]).show()
	}

	$(window).scrollTop(0);
	
}

$('body').on('click', '.page-link-num', function(evt) {
	evt.preventDefault();
	let btn = $(evt.target);
	
	show_next_results(btn);
});

// Listen for when plus button is clicked on ingredients form and add 
// another field 

function add_ingredient_fields() {
	let bottom = $('input.ing-form:visible').last();
	let del_btn = $('<i></i>');
	del_btn.addClass('bi bi-dash-circle');

	bottom.next().show();
	bottom.next().next().show();

	del_btn.insertBefore(bottom.next());

	hide_if_no_more();
}

// Hide plus button once all fields are visible

function hide_if_no_more() {
	if ($('.ing-form:hidden').length === 0) {
		$('.bi-plus-lg').hide();
	}
}

$('.bi-plus-lg').on('click', add_ingredient_fields);

// Button for removing optional ingredient fields after being added

function remove_ingredient_fields(btn) {
	let next = $(btn.next());
	
	next.hide();
	next.next().val('');
	next.next().hide();
	btn.remove();
}

$('#ingredients_form').on('click', '.bi-dash-circle', function(evt) {
	let btn = $(evt.target);
	
	remove_ingredient_fields(btn);
});

// Move search bar and logout, login and signup buttons to center
// when nav not collapsed
let clickable = true;
$('body').on('click', '.navbar-toggler-icon', function(evt) {
	let btn = $(evt.target);
	btn.attr('disabled', true)
	let classes = $('button.navbar-toggler').attr('class');

	while (clickable == true) {
		clickable = false;

		if (classes.search('collapsed'))  {
			$('div.search').toggleClass('justify-content-end');
			$('div.search').toggleClass('justify-content-center');
		} else {
			setTimeout(() => {
				$('div.search').toggleClass('justify-content-end');
				$('div.search').toggleClass('justify-content-center');
			}, 2000);
		}
	}
	
		
});

// If on mobile toggle smaller pagination element
if ($('body').width() < 1400) {
	$('ul.pagination').toggleClass('pagination-lg');
}


// Trigger share menu when share button clicked
$('body').on('click', 'a.share', function(evt) {
	if (navigator.share) {
		navigator.share({
			title: $('h2.card-title').text(),
			text: 'Check out this drink on Underground Mixology!',
			url: $(location).attr('href')
		})
	}
})
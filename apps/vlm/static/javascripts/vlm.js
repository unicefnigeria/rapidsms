$(document).ready(function() {
	$('.ward').click(function () {
		el = $(this).attr('id');
		children = '.'+el+'-hf';
		if ($(children).css('display') == 'table-row') {
			$(children).fadeOut('slow');
		} else {
			$(children).fadeIn('slow', function () { $(this).css('display', 'table-row'); });
		}
	});
});

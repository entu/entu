(function($) {
$.fn.placeholder = function(options) {
	var defaults = {css_class: "placeholder"};
	var options = $.extend(defaults, options);  
	this.each(function() {
		if ($(this).attr('placeholder') !== undefined) {
			var phvalue = $(this).attr("placeholder");
			var currvalue = $(this).attr("value");
			if (phvalue == currvalue) {
				$(this).addClass(options.css_class);
			}
			if (currvalue == "") {
				$(this).addClass(options.css_class);
				$(this).val(phvalue);
			}
			$(this).focusin(function(){
				var ph = $(this).attr("placeholder");
				if (ph == $(this).val()) {
					$(this).val("").removeClass(options.css_class);
				}
			});
			
			$(this).focusout(function(){
				var ph = $(this).attr("placeholder");
				if ($(this).val() == "") {
					$(this).val(ph).addClass(options.css_class);
				}
			});
		}
	});
	return this;
	};
})(jQuery);
/*******************************************************************************
 * dPassword v0.7 - delayed password masking (iPhone style)
 *                  jQuery plugin
 *
 * Usage:
 *    e.g. <code>$('input[type=password]').dPassword(options)</code>
 *    The options parameter is optional and can have the following optional entries:
 *        delay:					Number of seconds after which to hide input. Defaults to 1.
 *        observeForm:				Whether to automatically deactivate when parent form is submitted (default: true).
 *        form:						Form element different from parent form to observe for submitting (forces observeForm to true if set).
 *        cloakingCharacter:		Character to replace entered characters with. Defaults to the bullet (•).
 *        onChange:   				Handler when password has been changed.
 *        onStateChange:   			Handler when masking behaviour changes.
 *        switchToPasswordType:		Whether to switch input field back to password type on blur (looks bad in IE).
 *		  showIcon: 				Show a lock icon allowing the user to toggle masking behaviour (defaults to true).
 *									See further options
 * 										ICON_TITLE_ON, ICON_TITLE_OFF, ICON_PATH, ICON_STYLES, ICON_STYLES_ON, ICON_STYLES_OFF
 * 									for customization.
 *
 * Licensed under MIT License.
 *
 * Copyright (c) 2009 Stefan Ullrich, DECAF° | http://decaf.de
 *                    Dirk Schürjohann, DECAF° | http://decaf.de
 *                    Julian Dreissig
 *
 * Permission is hereby granted, free of charge, to any person obtaining 
 * a copy of this software and associated documentation files (the "Software"), 
 * to deal in the Software without restriction, including without limitation 
 * the rights to use, copy, modify, merge, publish, distribute, sublicense, 
 * and/or sell copies of the Software, and to permit persons to whom the 
 * Software is furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be 
 * included in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, 
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES 
 * OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. 
 * IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, 
 * DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR 
 * OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR 
 * THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 *
 * Known Issues: - view will not follow cursor if textfield is too small.
 *
 * @requires jQuery Library >= 1.3.2 (may work with older versions)
 */
(function() {
	jQuery.fn.dPassword = function(options) {
		
		// support multiple elements
	    if (this.length > 1) {
	        this.each(function() {jQuery(this).dPassword(options);});
	        return this;
	    }
    
		var options = jQuery.extend(defaultOptions, options);
		options.cloakingCharacter = options.cloakingCharacter.charAt(0);
	
		var _input = $(this);
		var _value = null,
			_previousInputValue = null,
			_timeout = null,
			_previousSelection = null,
			_options = null,
			_observing = false,
			_form = null,
			_toggleIcon = null,
			_keysDown = {},
			_inputFieldTypes = {};
			
		// register event listeners
		registerHandlers(_input);
		if (options.observeForm || options.form) {
			if (!_form) _form = options.form ? $(options.form) : _input.closest('form');
			if (_form) _form.bind("submit.dPassword", function(){deactivate(true);});
		}

		// create/handle toggle icon
		if (options.showIcon) {
			_toggleIcon = jQuery("<div class='dpassword-lock'></div>").insertAfter(_input);
			_toggleIcon.css({backgroundImage: "url(" + (options.iconPath || options.ICON_PATH) + ")"});
			_toggleIcon.css(options.ICON_STYLES);
			_toggleIcon.bind("click", function() {
				_observing ? deactivate() : activate();
				_input.focus();
			});
		}

		// TODO: public methods
		// TODO: possible to overwrite val() to outside?
	
 		activate();
		return this;
		
		// ------- method declarations follow ----------
	
		/**
		 * Returns the current value of the password field.
		 */
		function getValue() {
			return _observing ? _value : _input.val();
		}
	
		/**
		 * Switches to active mode. Will be automatically called on initialization.
		 * Use getValue() to retrieve field value once activated.
		 */
		function activate() {
			_observing = true;
			_value = _input.val();
			_cloakInput();
			if (_toggleIcon) _switchToggleIcon(true);
			if (options.onStateChange) options.onStateChange(_observing, this, _toggleIcon);
		}

		/**
		 * Deactivates dPassword temporarily/permanently and switches field back to normal password behaviour
		 * to e.g. perform DOM operations or value retrieval.
		 * IMPORTANT: If "temporarily" parameter is set to true will auto-reactivates on any input.
		 */
		function deactivate(temporarily) {
			if (_observing) {
				if (_timeout) {
					clearTimeout(_timeout);
					_timeout = null;
				}
				var selection = _getFieldSelection(_input);
				jQuery.browser.msie ? _switchInputTypeIE("password") : _input.get(0).setAttribute("type", "password");	// override jQuery's behaviour
				_input.val(getValue());
				if (document.activeElement && document.activeElement == _input) _setFieldSelection(_input, selection);
				if (temporarily !== true) {
					_observing = false;
					if (_toggleIcon) _switchToggleIcon(false);
					if (options.onStateChange) options.onStateChange(_observing, this, _toggleIcon);
				}
			}
		}

		function _keyDownHandler(event) {
			if (_observing) {
				if (!(_isSpecialKey(event.keyCode) || event.metaKey || event.ctrlKey)) {
					var keyCode = null;
					for (var keyCode in _keysDown) {
						_afterInputHandler(keyCode);
					}
					_storeSelection();
					if (!keyCode) _cloakInput();
					if (event.keyCode > 10) _keysDown[event.keyCode] = true;
				} else {
					_storeSelection();
					if (_timeout) {
						clearTimeout(_timeout);
						_timeout = null;
						_cloakInput();
					}
				}
			}
		}
	
		function _keyUpHandler(event) {
			if (_observing) {
				if (event.type == "paste") {
					setTimeout(_afterInputHandler, 0);
					return;
				}
		    	if (_isSpecialKey(event.keyCode) || event.metaKey || event.ctrlKey) return;
				if (_keysDown[event.keyCode] || event.keyCode < 11) _afterInputHandler(event);
			} else {
				var value = _input.val();
				if (value != _previousInputValue) {
					_previousInputValue = value;
					if (options.onChange) options.onChange(getValue());
				}
			}
		}

		function _afterInputHandler(keyCode) {
			delete _keysDown[keyCode];
			var value = _input.val();
			var selection = _getFieldSelection(_input);

			if (_previousInputValue != value) {
				var sStart = _previousSelection[0],
					sEnd = _previousSelection[1],
					sLength = _previousSelection[2],
					lengthDifference = value.length - _value.length,	// > 0: characters added
					newValue;			
				if (lengthDifference < 0 && sLength == 0) {		// single character deletion
					if (sStart == selection[0])	{				// forward deletion
						newValue = _value.substring(0, sStart) + _value.substring(sEnd + 1);
					} else {									// has to be backward deletion
						newValue = _value.substring(0, selection[0]) + _value.substring(sEnd);
					}
				} else {										// a selection has been replaced/deleted
					newValue = _value.substring(0, sStart) + value.substring(sStart, selection[1]) + _value.substring(sEnd);
				}
				_value = newValue;
				if (options.onChange) options.onChange(getValue());

				if (_timeout) {
					clearTimeout(_timeout);
					_timeout = null;
				}

				if (lengthDifference >= 0) {
					// leave newly written part uncloaked
					_cloakInput([sStart + 1, selection[1]]);
					_timeout = setTimeout(_cloakInput, options.delay * 1000);
				}
			} else {
				_previousSelection = selection;
			}
		}
				
		function registerHandlers(element) {
			element.bind("keydown.dPassword", _keyDownHandler);
			element.bind("keyup.dPassword paste.dPassword", _keyUpHandler);
			element.bind("select.dPassword focus.dPassword", _storeSelection);
			if (options.switchToPasswordType) {
				_input.bind("blur.dPassword", function() {deactivate(true);});		
			}	
		}
	
		function _storeSelection() {
			if (_observing)	_previousSelection = _getFieldSelection(_input);
		}
	
		function _cloakInput(keepRange) {
			var selection = _getFieldSelection(_input);
			var value = _input.val();
			if (keepRange) {
				_input.val(value.substring(0, keepRange[0] - 1 ).replace(/./g, options.cloakingCharacter) + value.substring(keepRange[0] - 1, keepRange[1]) + value.substring(keepRange[1]).replace(/./g, options.cloakingCharacter));
			} else {
				_input.val(value.replace(/./g, options.cloakingCharacter));
				if (_input.attr("type") != "text") {
					if (jQuery.browser.msie) {
						_switchInputTypeIE("text");
					} else {
						_input.get(0).setAttribute("type", "text");	// override jQuery's behaviour
					}
					_input.attr("autocomplete", "off");
				}
			}
			if (document.activeElement && document.activeElement == _input.get(0)) _setFieldSelection(_input, selection);
			_previousInputValue = _input.val();
		}
	

		function _switchInputTypeIE(toType) {
			// create input field (or retrieve from cache) with new type
			var newInput = _inputFieldTypes[toType];
			if (!newInput) {
				var tempDiv = _input.clone().wrap('<div></div>').parent();
				if (toType == "password") {
					tempDiv.html(tempDiv.html().replace(/>/, 'type="password">'));
				} else {
					tempDiv.html(tempDiv.html().replace(/type="?password"?/, 'type="text"'));
				}
				newInput = tempDiv.children();
				registerHandlers(newInput);
			}
			
			// update field
			newInput.css('width', (_input.get(0).clientWidth - 2*parseInt(_input.get(0).currentStyle.padding, 10)) + "px");
			newInput.css('height', (_input.get(0).clientHeight - 2*parseInt(_input.get(0).currentStyle.padding, 10)) + "px"); // fix different widths for password and text inputs in IE
			var oldInput = _input;
			oldInput.get(0).replaceNode(newInput.get(0));	// jQuery's replaceWith method gobbles the event handlers, apparently.
			_input = newInput;
			_input.val(oldInput.val());

			// first time here: store elements in cache
			if (!_inputFieldTypes) {
				_inputFieldTypes = {
					password: (toType == "password") ? newInput : oldInput,
					text: (toType == "password") ? oldInput : newInput
				};
			}
		}

		function _switchToggleIcon(state) {
			if (state) {
				_toggleIcon.css(options.ICON_STYLES_OFF).css({className: "dpassword-lock-closed"});
				_toggleIcon.attr('title', options.ICON_TITLE_ON);
			} else {
				_toggleIcon.css(options.ICON_STYLES_ON).css({className: "dpassword-lock-closed"});
				_toggleIcon.attr('title', options.ICON_TITLE_OFF);
			}
		}
	};
	
	var defaultOptions = {
		delay: 1,
		observeForm: true,					 
		form: null,							 
		cloakingCharacter: (navigator.platform == "MacIntel") ? '\u2022' : '\u25CF',		 
		onChange: null,
		onStateChange: null,
		showIcon: true,
		switchToPasswordType: !jQuery.browser.msie,		
		/*
		 * Default styles and behaviours for lock icon, see showIcon option.
		 * Override at will.
		 */
		ICON_TITLE_ON: "Delayed masking active, click here to switch off.",
		ICON_TITLE_OFF: "Click to activate delayed masking of input.",
		ICON_STYLES: {
			display: "inline",
			position: "absolute",
			width: "16px", height: "16px",
			margin: "-10px 0 0 -12px",
			overflow: "hidden", cursor: "pointer",
			backgroundRepeat: "no-repeat"
		},
		ICON_PATH: "lock.gif",		// set to your position of icon
		ICON_STYLES_OFF: {
			backgroundPosition: "0 0"
		},
		ICON_STYLES_ON: {
			backgroundPosition: "0 -16px"
		}
	};
	
	function _getFieldSelection(element) {
		if (document.selection) {
			var range = document.selection.createRange();
			var length = range.text.length;
			range.moveStart('character', -element.val().length);	// Move selection start to 0 position
			var cursorPos = range.text.length;	// The caret position is now the selection length
			return [cursorPos - length, cursorPos, length];
		} else {
			var el = element.get(0);
			return [el.selectionStart, el.selectionEnd, el.selectionEnd - el.selectionStart];
		}
	}
	
	function _setFieldSelection(element, selection) {
		var el = element.get(0);
		if (document.selection) {
			var range = el.createTextRange();
			range.collapse();
			range.moveStart('character', selection[0]);
			range.moveEnd('character', selection[1] - selection[0]);
			range.select();
		} else {
			el.selectionStart = selection[0];
			el.selectionEnd = selection[1];
		}
	}
	
	function _isSpecialKey(keyCode) {
		// TODO: Need to check OS? Windows key?
		return (keyCode >= 9 && keyCode <= 20) || (keyCode >= 33 && keyCode <= 40) || keyCode == 224;
	}
})();
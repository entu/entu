//@codekit-prepend "jquery.autocomplete.js";
//@codekit-prepend "date-et-EE.js";
//@codekit-prepend "jQuery.dPassword.js";
//@codekit-prepend "chosen.jquery.js";
//@codekit-prepend "jquery.elastic.source.js";
//@codekit-prepend "jquery.placeholder.js";
//@codekit-prepend "jquery.raty.js";
//@codekit-prepend "jquery.simplemodal-1.4.1.js";
//@codekit-prepend "jstorage.js";


function removeBubbleInfo(key) {
    $.jStorage.deleteKey('BubbleInfo_' + key);
}

function getBubbleInfo(bubbletype, key, div, listtype) {
    bubble_json = $.jStorage.get('BubbleInfo_' + key);
    if (bubble_json) {
        makeBubbleInfo(bubbletype, bubble_json, div, listtype)
    } else {
        $.post('/bubble/x', {key: key}, function(bubble_json) {
            makeBubbleInfo(bubbletype, bubble_json, div, listtype);
            $.jStorage.set('BubbleInfo_' + bubble_json.key, bubble_json);
            //$.jStorage.setTTL('BubbleInfo_' + bubble_json.key, 300000)
        }, 'json');
    }
};

function makeBubbleInfo(bubbletype, bubble_json, div, listtype) {
    if(bubble_json.image) {
        image = '<img src="'+bubble_json.image+'" />';
    } else {
        image = '';
    };
    if(bubble_json.info) {
        info = '<span>'+bubble_json.info+'</span>';
    } else {
        info = '';
    };
    if(bubble_json.count) {
        count = '<div>'+bubble_json.count+'</div>';
    } else {
        count = '';
    };
    if(listtype == 'searchlist') {
        $(div).html(count+image+bubble_json.title+info);
        $(div).attr('href', '#'+bubble_json.id);
        $(div).removeClass('empty_item');
        if('#'+bubble_json.id == window.location.hash) {
            $(div).addClass('active');
        };
    };
    if(listtype == 'accordion') {
        $(div).html(bubble_json.title+info);
        if (bubble_json.type == bubbletype) {
            $(div).attr('href', '#'+bubble_json.id);
            $(div).addClass('open_subbubble');
        } else {
            $(div).attr('href', '/bubble/'+bubble_json.type+'#'+bubble_json.id);
        };
    };
};



function getChoices(property) {
    choices_json = $.jStorage.get('Choices_' + property);
    if (choices_json) {
        makeChoices(choices_json)
    } else {
        $.post('/bubble/sfv', { 'property': property }, function(choices_json) {
            makeChoices(choices_json);
            $.jStorage.set('Choices_' + choices_json.property, choices_json);
            //$.jStorage.setTTL('Choices_' + choices_json.property, 300000)
        }, 'json');
    };
};

function makeChoices(choices_json) {
    $('select[name='+choices_json.property+']').each(function() {
        selectbox = $(this);
        for (i in choices_json.values) {
            item = choices_json.values[i];
            if(selectbox.data('oldvalue').indexOf(item.key) != -1) {
                selected = ' selected';
            } else {
                selected = '';
            }
            selectbox.width(selectbox.parent().width());
            selectbox.append('<option value="'+item.key+'"'+selected+'>'+item.value+'</option>');
            selectbox.chosen({
                allow_single_deselect: true,
            });
            selectbox.prev('img').hide();
            selectbox.trigger('liszt:updated');
        };
    });
};



function openDropdown(url, onclose) {
    document.body.style.cursor = 'wait';
    $('#dropdown_content').html('');
    $('#dropdown_spinner').show();
    $("#dropdown").modal({
        position: [0,50],
        opacity: 30,
        overlayCss: {backgroundColor:"#000000"},
        escClose: true,
        overlayClose: true,
        onClose: onclose,
    });
    $.get(url, function(data) {
        document.body.style.cursor = 'default';
        $('#dropdown_spinner').hide();
        $("#dropdown_content").html(data);
        if($('#dropdown_content').height() > $(window).height()*0.9) {
            $('#dropdown_content').css('overflow-x', 'hidden');
            $('#dropdown_content').css('overflow-y', 'auto');
            $('#dropdown_content').css('max-height', $(window).height()*0.9);
        };
    });
};

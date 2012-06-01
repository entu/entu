function removeBubbleInfo(key) {
    //$.jStorage.deleteKey('BubbleInfo_' + key);
};

function getEntityInfo(bubbletype, id, div, listtype) {
    entity_json = '';// $.jStorage.get('BubbleInfo_' + key);
    if (entity_json) {
        makeEntityInfo(bubbletype, entity_json, div, listtype)
    } else {
        $.post('/entity-'+id+'/listinfo', function(entity_json) {
            makeEntityInfo(bubbletype, entity_json, div, listtype);
            //$.jStorage.set('BubbleInfo_' + entity_json.key, entity_json);
            //$.jStorage.setTTL('BubbleInfo_' + entity_json.key, 300000)
        }, 'json');
    }
};

function makeEntityInfo(bubbletype, entity_json, div, listtype) {
    if(entity_json.image) {
        image = '<img src="'+entity_json.image+'" />';
    } else {
        image = '';
    };
    if(entity_json.info) {
        info = '<span>'+entity_json.info+'</span>';
    } else {
        info = '';
    };
    if(entity_json.count) {
        count = '<div>'+entity_json.count+'</div>';
    } else {
        count = '';
    };
    if(listtype == 'searchlist') {
        $(div).html(count+image+entity_json.title+info);
        $(div).attr('href', '#'+entity_json.id);
        $(div).removeClass('empty_item');
        if('#'+entity_json.id == window.location.hash) {
            $(div).addClass('active');
        };
    };
    if(listtype == 'accordion') {
        $(div).html(entity_json.title+info);
        if (entity_json.type == bubbletype) {
            $(div).attr('href', '#'+entity_json.id);
            $(div).addClass('open_subbubble');
        } else {
            $(div).attr('href', '/bubble/'+entity_json.type+'#'+entity_json.id);
        };
    };
};



function getChoices(property) {
    choices_json = '';// $.jStorage.get('Choices_' + property);
    if (choices_json) {
        makeChoices(choices_json)
    } else {
        $.post('/bubble/sfv', { 'property': property }, function(choices_json) {
            makeChoices(choices_json);
            //$.jStorage.set('Choices_' + choices_json.property, choices_json);
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

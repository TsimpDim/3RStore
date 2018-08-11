$(document).ready(function(){
    $('#search_input').on('input', initiateSearch);
    $('input').on('input', checkDisabled);
    $('.show-note').on('click', showNote);
});


function containsOtherArray(thisArray, otherArray){
    for(let i = 0; i < thisArray.length; i++){
      if(otherArray.indexOf(thisArray[i]) === -1)
        return false;
    }
    return true;
}

function initiateSearch(){
    let inputTags = $('#search_input').val().toLowerCase().split(','); // Array with requested tags
    let resources = $('.re_card'); // Array with resources
    let filters;
    let useFilters = false;

    if($('#search_input').val().indexOf('-') > -1){
        useFilters = true;
        filters  = $('#search_input').val().toLowerCase().split('-')[1].split(',');
        inputTags = $('#search_input').val().toLowerCase().split('-')[0].trim().split(',');
    }

    if(inputTags.length == 1 && inputTags[0] == ""){ // If no tags have been entered
        $("#cards_cont").show(); // Show all the resources
        $('.re_card').show();
    }else{
        resources.each(function(){
            
            let tags = $(this).find('.re_tags'); 
            let resTagArray = [];
            let cur_r_title = $(this).find('h4 > a').text().toLowerCase();

            // Get a cleaned up array of the given (by the user) tags
            tags.each(function(i){
                let curr_tag = $(this).text().trim();
                if(curr_tag != null || curr_tag.length > 0)
                    resTagArray.push(curr_tag);
            });

            // Show the resource if the tags match or if the title includes the input
            if(containsOtherArray(inputTags, resTagArray) || cur_r_title.includes(inputTags[0])){
                if(useFilters && !checkFilters(resTagArray, filters))
                $(this).hide();
                else{
                    $(this).show();
                    $("#cards_cont").show();
                }
            }else
                $(this).hide();
        });

        if($("#cards_cont").children(':visible').length == 0)
            $("#cards_cont").hide();
        else
            $("#cards_cont").show();
    }
}

function checkDisabled(){

    if ($(this).attr('name') == 'incl' && $(this).val().length > 0){
        $("input[name='excl']").prop('disabled', true);
    }else{
        $("input[name='excl']").prop('disabled', false);
    }

    if ($(this).attr('name') == 'excl' && $(this).val().length > 0){
        $("input[name='incl']").prop('disabled', true);
    }else{
        $("input[name='incl']").prop('disabled', false);
    }

}

function showNote(){
    let cur_id = $(this).data('id'); // Element of button
    let master = $('#' + cur_id); // Find parent element

    let text = master.find('.card-footer').text(); // Get the text
    text = text.replace(/<\/br\>/g, '\n'); // Properly show the text
    alert(text);
}

function checkFilters(tags, filter){

    let include = true;

    tags.forEach(function(i){
        if(filter.includes(i))
            include = false;
    });

    return include;
}
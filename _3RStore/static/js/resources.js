$(document).ready(function(){
    $('#search_input').on('input', initiateSearch);
    $('input').on('input', checkDisabled);
    $('.copy_link').on('click', copyLink);
});


function initiateSearch(){
    let inputTags = $('#search_input').val().toLowerCase().split(','); // Array with requested tags
    let resources = $('.re_cards'); // Array with resources
    let filters;
    let useFilters = false;

    if($('#search_input').val().indexOf('-') > -1){
        useFilters = true;
        filters  = $('#search_input').val().toLowerCase().split('-')[1].split(',');
        inputTags = $('#search_input').val().toLowerCase().split('-')[0].trim().split(',');
    }


    if(inputTags.length == 1 && inputTags[0] == ""){ // If no tags have been entered
        $('.re_cards').show(); // Show all the resources
    }else{
        resources.each(function(){
            
            let tags = $(this).find('.re_tags'); 
            let resTagArray = [];
            let curResTitle = $(this).find('h4 > a').text().toLowerCase();

            // Get a cleaned up array of the given (by the user) tags
            tags.each(function(i){
                let curTag = $(this).text().trim();
                if(curTag != null || curTag.length > 0)
                    resTagArray.push(curTag);
            });

            // Show the resource if the tags match or if the title includes the input
            if((containsOtherArray(inputTags, resTagArray) || curResTitle.includes(inputTags[0]))){
                if(useFilters && !checkFilters(resTagArray, filters))
                    $(this).hide();
                else
                    $(this).show();

            }else
                $(this).hide();

        });
    }
}

function containsOtherArray(thisArray, otherArray){
    for(let i = 0; i < thisArray.length; i++){
      if(otherArray.indexOf(thisArray[i]) === -1)
         return false;
    }
    return true;
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

function checkFilters(tags, filter){

    let include = true;

    tags.forEach(function(i){
        if(filter.includes(i))
            include = false;
    });

    return include;
}

function copyLink(){
    let link = $(this).data('link');

    let el = document.createElement('input');
    el.value = link;

    document.body.appendChild(el);
    el.select();

    document.execCommand('copy');

    document.body.removeChild(el);
}
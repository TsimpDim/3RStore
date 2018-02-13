$(document).ready(function(){
    $('#search_input').on('input',initiateSearch);
});


function containsOtherArray(thisArray, otherArray){
    for(let i = 0; i < thisArray.length; i++){
      if(otherArray.indexOf(thisArray[i]) === -1)
         return false;
    }
    return true;
}

function initiateSearch(){
    let input = $('#search_input').val().toLowerCase().split(','); // Array with requested tags
    let resources = $('.re_cards'); // Array with resources

    if(input.length == 1 && input[0] == ""){ // If no tags have been entered
        $('.re_cards').show(); // Show all the resources
    }else{
        resources.each(function(){
            
            let tags = $(this).find('.re_tags'); 
            let tag_array = [];
            let cur_r_title = $(this).find('h4 > a').text().toLowerCase();

            // Get a cleaned up array of the given (by the user) tags
            tags.each(function(i){
                let curr_tag = $(this).text().trim();
                if(curr_tag != null || curr_tag.length > 0)
                    tag_array.push(curr_tag);
            });

            // Show the resource if the tags match or if the title includes the input
            if(containsOtherArray(input, tag_array) || cur_r_title.includes(input[0]))
                $(this).show();
            else
                $(this).hide();

        });
    }
}
$(document).ready(function(){

    $('#search').keyup(function(){
        let input = $('#search').val().toLowerCase().split(','); // Array with requested tags
        let resources = $('.list-group-item.active'); // Array with resources

        if(input.length == 1 && input[0] == ""){ // If no tags have been entered
            $('.list-group').show(); // Show all the resources
        }else{
            resources.each(function(){
                
                let tags = $(this).children('.label.label-default');
                let tag_array = [];
                let curr_resource = $(this).parent();
                let curr_resource_title = $(this).children('h3').children('.re_title').text().toLowerCase();

                tags.each(function(i){
                    let curr_tag = $(this).text().toLowerCase().trim();
                    if(curr_tag != null || curr_tag.length > 0)
                        tag_array.push(curr_tag);
                });

                if(containsOtherArray(input, tag_array) || curr_resource_title.includes(input[0]))
                    curr_resource.show();
                else
                    curr_resource.hide();

            });
        }
    });

});


function containsOtherArray(thisArray, otherArray){
    for(var i = 0; i < thisArray.length; i++){
      if(otherArray.indexOf(thisArray[i]) === -1)
         return false;
    }
    return true;
  }
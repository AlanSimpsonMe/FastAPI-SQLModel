// Executes after page loads
document.addEventListener("DOMContentLoaded", function(){
    // Any javascript code you put here executes when any layout page opens

});

// Show or hide the section that asks for delete confimation
function show_confirm(show) {
    document.getElementById('confirm-delete').style.display = show ? "block" : "none";
}
function delete_video(video_id){
    // Mark a video for deletion by browsing to delete_form_video endpoint with video id 
    base_url=location.origin;
    target_url = base_url + '/delete_form_video/' + video_id;
    location.href = target_url;
}

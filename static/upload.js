$(function () {
  $('#drop-area').dmUploader({
    url: '/upload',
    auto: true,
    queue: false,
    onDragEnter: function(){
      this.addClass('drop-active');
    },
    onDragLeave: function(){
      this.removeClass('drop-active');
    },
    // onComplete: function () {
    //   console.log('All pending tranfers');
    // },
    onNewFile: function (id, file) {
      add_file(id, file);
    },
    onBeforeUpload: function (id) {
      uploading = 1;
      document.getElementById("drop-area").style.display = "none";
      document.getElementById("uploading-list").style.display = "block";
      console.log('Starting upload ' + id);
    },
    onUploadProgress: function (id, percent) {
      file_progress(id, percent);
    },
    onUploadSuccess: function (id, data) {
      console.log('Server Response for file #' + id + ': ' + JSON.stringify(data));
      uploaded_count++
      if(uploaded_count >= file_count){
        setTimeout(function(){
          location.reload();
        }, 300);
      }
    },
    onUploadError: function (id, xhr, status, message) {
      Swal.fire("Error", "Something went wrong", "error");
    },
    onFallbackMode: function () {
      Swal.fire("Error", "Something went wrong", "error");
    },
  });
});
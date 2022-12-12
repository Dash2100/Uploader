$(function () {
  $('#drop-area').dmUploader({
    url: '/admin/upload',
    auto: true,
    queue: false,
    onDragEnter: function(){
      $(".upload-options-area").hide();
      this.addClass('drop-active');
    },
    onDragLeave: function(){
      this.removeClass('drop-active');
    },
    onNewFile: function (id, file) {
      add_file(id, file);
    },
    onBeforeUpload: function (id) {
      uploading = 1;
      $("#drop-area").hide();
      $('#uploading-list').show();
      $('.upload-options').hide();
      $(".upload-options-area").hide();
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
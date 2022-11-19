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
    onComplete: function () {
      console.log('All pending tranfers');
    },
    onNewFile: function (id, file) {
      console.log(id, file);
      add_file(id, file);
    },
    onBeforeUpload: function (id) {
      uploading = 1;
      document.getElementById("drop-area").style.display = "none";
      document.getElementById("uploading-list").style.display = "block";
      console.log('Starting upload');
    },
    onUploadCanceled: function (id) {
      // ui_multi_update_file_status(id, 'warning', 'Canceled by User');
      // ui_multi_update_file_progress(id, 0, 'warning', false);
    },
    onUploadProgress: function (id, percent) {
      // ui_multi_update_file_progress(id, percent);
      console.log(id, percent);
    },
    onUploadSuccess: function (id, data) {
      console.log('Server Response for file #' + id + ': ' + JSON.stringify(data));
      console.log('Upload of file #' + id + ' COMPLETED');
      // ui_multi_update_file_status(id, 'success', 'Upload Complete');
      // ui_multi_update_file_progress(id, 100, 'success', false);
    },
    onUploadError: function (id, xhr, status, message) {
      // ui_multi_update_file_status(id, 'danger', message);
      // ui_multi_update_file_progress(id, 0, 'danger', false);
    },
    onFallbackMode: function () {
      Swal.fire("Error", "Something went wrong", "error");
    },
  });
});
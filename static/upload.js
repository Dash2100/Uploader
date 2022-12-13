let sharestate = "Default";

$(function () {
  $('#drop-area').dmUploader({
    url: '/admin/upload',
    auto: true,
    queue: false,
    onDragEnter: function () {
      $(".upload-options-area").hide();
      this.addClass('drop-active');
    },
    onDragLeave: function () {
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
    extraData: function() {
      if ($('#upload-share-check').is(":checked") === true) {
        sharestate = 1;
      } else {
        sharestate = 0;
      }
      return {
        "share": sharestate
      };
    },
    onUploadProgress: function (id, percent) {
      file_progress(id, percent);
    },
    onUploadSuccess: function (id, data) {
      console.log('Server Response for file #' + id + ': ' + JSON.stringify(data));
      uploaded_count++
      if (uploaded_count >= file_count) {
        setTimeout(function () {
          location.reload();
        }, 300);
      }
    },
    onUploadError: function (id, xhr, status, message) {
      Swal.fire({
        title: "Error",
        text: message,
        icon: "error",
        allowOutsideClick: false,
        allowEscapeKey: false,
        allowEnterKey: false,
        showConfirmButton: true,
        confirmButtonText: "Reload Page",
        confirmButtonColor: "#546ad8",
      }).then((result) => {
        if (result.isConfirmed) {
          location.reload();
        }
      }
      );
    },
    onFallbackMode: function () {
      Swal.fire({
        title: "Error",
        text: "Your browser does not support drop file uploads.",
        icon: "error",
        allowOutsideClick: false,
        allowEscapeKey: false,
        allowEnterKey: false,
        showConfirmButton: true,
        confirmButtonText: "Reload Page",
        confirmButtonColor: "#546ad8",
      }).then((result) => {
        if (result.isConfirmed) {
          location.reload();
        }
      }
      );
    },
  });
});
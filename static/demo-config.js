$(function(){
  $('#drag-and-drop-zone').dmUploader({ //
    url: '/upload',
    auto: true,
    queue: false,
    onDragEnter: function(){
      this.addClass('active');
    },
    onDragLeave: function(){
      this.removeClass('active');
    },
    onComplete: function(){
      console.log('All pending tranfers');
    },
    onNewFile: function(id, file){
      console.log('New file added #');
      ui_multi_add_file(id, file);
    },
    onBeforeUpload: function(id){
      console.log('Starting the upload of #');
      ui_multi_update_file_status(id, 'uploading', 'Uploading...');
      ui_multi_update_file_progress(id, 0, '', true);
    },
    onUploadCanceled: function(id) {
      ui_multi_update_file_status(id, 'warning', 'Canceled by User');
      ui_multi_update_file_progress(id, 0, 'warning', false);
    },
    onUploadProgress: function(id, percent){
      ui_multi_update_file_progress(id, percent);
      console.log(id, percent);
    },
    onUploadSuccess: function(id, data){
      console.log('Server Response for file #' + id + ': ' + JSON.stringify(data));
      console.log('Upload of file #' + id + ' COMPLETED');
      ui_multi_update_file_status(id, 'success', 'Upload Complete');
      ui_multi_update_file_progress(id, 100, 'success', false);
    },
    onUploadError: function(id, xhr, status, message){
      ui_multi_update_file_status(id, 'danger', message);
      ui_multi_update_file_progress(id, 0, 'danger', false);  
    },
    onFallbackMode: function(){
      // When the browser doesn't support this plugin :(
        console.log('Plugin cant be used here, running Fallback callback');
    },
    onFileSizeError: function(file){
      console.log('File \'' + file.name + '\' cannot be added: size excess limit');
    }
  });
});
let uploading = 0;
let file_count = 0;
let uploaded_count = 0;

function $id(id) {
  return document.getElementById(id);
}

// popup
function upload() {
  $id('upload-area').style.display = 'block';
  var x = document.getElementsByClassName("popup")[0];
  x.classList.add("popup--opened");
}

function popopoff() {
  if (uploading == 0) {
    var x = document.getElementsByClassName("popup")[0];
    x.classList.remove("popup--opened");
  }
}

function downloadFile(fileName) {
  let url = '/download/' + fileName;
  let a = document.createElement('a');
  a.href = url;
  a.download = fileName;
  a.click();
};

function delFile(fileName) {
  Swal.fire({
    title: 'Delete?',
    text: "You won't be able to revert this!",
    icon: 'warning',
    showCancelButton: true,
    confirmButtonColor: '#d33',
    cancelButtonColor: '#51597e',
    confirmButtonText: 'Yes'
  }).then((result) => {
    if (result.isConfirmed) {
      $.ajax({
        url: "/delfile/" + fileName,
        method: "get",
        success: function (res) {
          if (res == "OK") {
            location.reload();
          }
          if (res == "Not Found") {
            Swal.fire("Error", "File not found", "error");
          }
          if (res == "Not authorized") {
            Swal.fire("Error", "You are not authorized", "error");
          }
        },
        error: function (res) {
          alert("Something went wrong");
        }
      });
    }
  })
}

// ui

function add_file(id, file){
  file_count++;
  var template = $('#files-template').text();
  template = template.replace('%%filename%%', file.name);
  template = $(template);
  template.prop('id', 'file-' + id);

  $id('uploading-list').appendChild(template[0]);
}

function file_progress(id, percent){
  var file = $id('file-' + id);
  var progress = file.querySelector('.progressbar');
  progress.style.width = percent + '%';
  if(percent===100){
    uploaded_count++;
    if(uploaded_count >= file_count){
      location.reload();
    }
    progress.style.backgroundColor = '#546ad8';
  }
}
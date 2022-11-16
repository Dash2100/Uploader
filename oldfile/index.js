let downloading = 0;

function Init() {
  let dropArea = document.getElementById('drop-area')

  dropArea.addEventListener('dragenter', handleEnter, false)
  dropArea.addEventListener('dragleave', handleLeave, false)
  dropArea.addEventListener('dragover', handleDragover, false)
  dropArea.addEventListener('drop', handleDrop, false)

    ;['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
      dropArea.addEventListener(eventName, preventDefaults, false)
    })

  function preventDefaults(e) {
    e.preventDefault()
    e.stopPropagation()
  }
}

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
  if (downloading == 0) {
    var x = document.getElementsByClassName("popup")[0];
    x.classList.remove("popup--opened");
  }
}


function download(name) {
  window.location.href = "/download/" + name;
}

function handleEnter(e) {
  $id('drop-area').style.background = '#455399';
}

function handleLeave(e) {
  $id('drop-area').style.background = '#363c5a';
}

function handleDragover(e) {
  $id('drop-area').style.background = '#455399';
}

function handleDrop(e) {
  let dt = e.dataTransfer
  let files = dt.files
  handleFiles(files)
}

totalsize = 0
file_length = 0
function handleFiles(files) {
  // console.log(files);
  $id('drop-area').style.background = '#363c5a';
  $id('drop-area').style.display = 'none';
  $id('uploading').style.display = 'block';
  files = [...files]
  file_length = files.length;
  files.forEach(file =>
    totalsize = totalsize + file.size
  );
  files.forEach(file =>
    uploadFile(file)
  );
}


uploaded = 0
function uploadFile(file) {
  downloading = 1;
  console.log(totalsize);
  // $id('uploading_name').innerHTML = flen + " files uploading...";
  var url = "/upload";
  var xhr = new XMLHttpRequest();
  var fd = new FormData();
  xhr.upload.addEventListener("progress", progressHandler, false);
  xhr.addEventListener("load", completeHandler, false);
  xhr.addEventListener("error", errorHandler, false);
  xhr.addEventListener("abort", abortHandler, false);
  xhr.open("POST", url);
  fd.append('file', file);
  xhr.send(fd);
}

upsize = 0
function progressHandler(event) {
  var percent = (event.loaded / event.total) * 100;
  console.log(percent);
  // $id('uploading_name').innerHTML = `Uploaded ${upsize} bytes of ${totalsize} (${uploaded} / ${file_length})`;
  // var percent = (upsize / totalsize) * 100;
  // $id("progressbar").style.width = String(Math.round(percent)) + "%";
}


function completeHandler(event) {
  uploaded = uploaded + 1;
  if (uploaded >= file_length) {
    downloading = 0;
    // Swal.fire("Upload", "ok", "success")
    console.log("all uploaded");
  }
  console.log(`${uploaded} Uploaded`)
}

function errorHandler(event) {
  console.log("error")
}

function abortHandler(event) {
  console.log("abort")
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
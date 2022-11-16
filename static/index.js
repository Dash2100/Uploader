downloading = 0

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
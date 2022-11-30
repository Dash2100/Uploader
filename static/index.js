let uploading = 0;
let file_count = 0;
let uploaded_count = 0;
let sharebutton;
let linkbutton;

let linkstate;

function $id(id) {
  return document.getElementById(id);
}

function init() {
  var domain = window.location.hostname;
  $('#baseurl').text(domain + ' /');
}

// popup
function upload() {
  $id('modfile-area').style.display = 'none';
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
  let url = '/admin/download/' + fileName;
  let a = document.createElement('a');
  a.href = url;
  a.download = fileName;
  a.click();
};

function delFile(filename) {
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
        url: "/admin/delfile",
        method: "post",
        data: JSON.stringify({ filename: filename }),
        contentType: "application/json;charset=utf-8",
        success: function (res) {
          if (res == "OK") {
            location.reload();
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

function add_file(id, file) {
  file_count++;
  var template = $('#files-template').text();
  template = template.replace('%%filename%%', file.name);
  template = $(template);
  template.prop('id', 'file-' + id);

  $id('uploading-list').appendChild(template[0]);
}

function file_progress(id, percent) {
  var file = $id('file-' + id);
  var progress = file.querySelector('.progressbar');
  progress.style.width = percent + '%';
  if (percent === 100) {
    progress.style.backgroundColor = '#546ad8';
  }
}

function modify(name) {
  sharebutton = 0;
  linkbutton = 0;
  linkstate = 0;
  filestate(name);
  $('#link-input').hide();
  $id('upload-area').style.display = 'none';
  $id('modfile-area').style.display = 'block';
  $id('savechange').onclick = function () { save(name); };
  $id('delfile').onclick = function () { delFile(name); };
  $id('modfile-name').innerHTML = name;
  var x = document.getElementsByClassName("popup")[0];
  x.classList.add("popup--opened");
}

function filestate(filename) {
  $.ajax({
    url: "/admin/filestate",
    method: "post",
    contentType: "application/json;charset=utf-8",
    data: JSON.stringify({ filename: filename }),
    success: function (res) {
      var res = JSON.parse(res);
      sharebutton = res.share;
      linkstate = res.link;
      if (res.share === 1) {
        $('#Share-check').prop('checked', true);
      } else {
        $('#Share-check').prop('checked', false);
      }
      if (res.link != "") {
        linkbutton = 1;
        $('#Share-link-check').prop('checked', true);
        $('#link-input').show();
        $('#shortlink').val(res.link);
      } else {
        linkbutton = 0;
        $('#Share-link-check').prop('checked', false);
        $('#link-input').hide();
        $('#shortlink').val("");
      }
    }
  });
}

function save(filename) {
  var shortlink = $('#shortlink').val();
  if ($('#Share-check').is(":checked") === true) {
    var sstate = 1;
  } else {
    var sstate = 0;
  }
  if ($('#Share-link-check').is(":checked") === true) {
    var lstate = 1;
  } else {
    var lstate = 0;
  }
  if (sharebutton != sstate) {
    $.ajax({
      url: "/admin/share",
      method: "post",
      data: JSON.stringify({ filename: filename, state: sstate }),
      contentType: "application/json;charset=utf-8",
      success: function (res) {
        if (res == "OK") {
          popopoff();
        }
      }
    });
  }
  if (lstate === 1) {
    if (linkstate != shortlink) {
      $.ajax({
        url: "/admin/shortlink",
        method: "post",
        data: JSON.stringify({ shortlink: shortlink, filename: filename }),
        contentType: "application/json;charset=utf-8",
        success: function (res) {
          if (res == "OK") {
            popopoff();
          }
          if (res == "Already in use") {
            Swal.fire({
              icon: 'error',
              title: 'Oops...',
              text: 'This shortlink already in use!',
            })
          }
        }
      });
    }
    else{
      popopoff();
    }
  }
  else {
    $.ajax({
      url: "/admin/delshortlink",
      method: "post",
      data: JSON.stringify({ filename: filename }),
      contentType: "application/json;charset=utf-8",
      success: function (res) {
        if (res == "OK") {
          popopoff();
        }
      }
    });
  }
}
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
  hideall();
  $id('upload-area').style.display = 'block';
  var x = document.getElementsByClassName("popup")[0];
  x.classList.add("popup--opened");
}

function popupoff() {
  if (uploading == 0) {
    var x = document.getElementsByClassName("popup")[0];
    x.classList.remove("popup--opened");
  }
}

function hideall(){
  $id('modfile-area').style.display = 'none';
  $id('upload-area').style.display = 'none';
  $id('multi-modfile-area').style.display = 'none';
}

function modify(name) {
  sharebutton = 0;
  linkbutton = 0;
  linkstate = 0;
  hideall();
  filestate(name);
  $('#link-input').hide();
  $id('modfile-area').style.display = 'block';
  $id('savechange').onclick = function () { save(name); };
  $id('delfile').onclick = function () { delFile(name); };
  $id('modfile-name').innerHTML = name;
  var x = document.getElementsByClassName("popup")[0];
  x.classList.add("popup--opened");
}

function multimodify() {
  hideall();
  $id('multi-modfile-area').style.display = 'block';
  $('#multi-Share-check').prop('checked', false);
  $id('multi-modfile-name').innerHTML = selected.length + " Files";
  var x = document.getElementsByClassName("popup")[0];
  x.classList.add("popup--opened");
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
    confirmButtonText: 'Yes',
    allowEnterKey: false,
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
          Swal.fire({
            title: "Error",
            text: "Something went wrong, please try again later.",
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
          popupoff();
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
            popupoff();
          }
          if (res == "Already in use") {
            Swal.fire({
              icon: 'error',
              title: 'Oops...',
              text: 'This shortlink already in use!',
            })
          }
          if (res == "Empty") {
            Swal.fire({
              icon: 'error',
              title: 'Oops...',
              text: 'You must enter a shortlink!',
            })
          }
          if (res == "illegal") {
            $('#shortlink').val("");
            Swal.fire({
              icon: 'error',
              title: 'Wait!',
              text: "The shortlink can't contain special characters or spaces",
            })
          }
        }
      });
    }
    else {
      popupoff();
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
          popupoff();
        }
      }
    });
  }
}

let selecting = 0;
function selectfile() {
  selecting = 1
  $('.modfile-icon').addClass('hide');
  $('.file-card').addClass('file-card-disable');
  $('.file').addClass('file-select');
  $('.opt-icons').addClass('hide');
  $('.act-icons').addClass('show');
}

let selected = [];
function cancelselect() {
  selecting = 0;
  selected = [];
  $('.modfile-icon').removeClass('hide');
  $('.file-card').removeClass('file-card-disable');
  $('.file').removeClass('file-select');
  $('.opt-icons').removeClass('hide');
  $('.file-selected').removeClass('file-selected');
  $('.act-icons').removeClass('show');
  $('.edit-options').removeClass('edit-options-open');
}

function select(filename) {
  if (selecting === 1) {
    if (selected.includes($('#' + filename + "-name").text())) {
      selected.splice(selected.indexOf(filename), 1);
      $("#" + filename).removeClass('file-selected');
      $("#" + filename + "-card").removeClass('file-card-selected');
      $("#" + filename + "-card").addClass('file-card-disable');
      if (selected.length < 1) {
        $('.edit-options').removeClass('edit-options-open');
      } else {
        $('#edit-options-text').text(selected.length + " Files selected");
      }
    }
    else {
      selected.push($('#' + filename + "-name").text());
      if (selected.length > 0) {
        $('.edit-options').addClass('edit-options-open');
      }
      $("#" + filename).addClass('file-selected');
      $("#" + filename + "-card").removeClass('file-card-disable');
      $("#" + filename + "-card").addClass('file-card-selected');
      $('#edit-options-text').text(selected.length + " Files selected");
    }
  }
}

function multidelete() {
  Swal.fire({
    title: "Are you sure?",
    text: "This will delete " + selected.length + " files",
    icon: "warning",
    showCancelButton: true,
    confirmButtonColor: "#d33",
    confirmButtonText: "Delete",
    allowEnterKey: false,
  }).then((result) => {
    if (result.isConfirmed) {
      $.ajax({
        url: "/admin/multidelete",
        method: "post",
        data: JSON.stringify({ files: selected }),
        contentType: "application/json;charset=utf-8",
        success: function (res) {
          if (res == "OK") {
            location.reload();
          }
        }
      });
    }
  })
}

function multishare(){
  if ($('#multi-Share-check').is(":checked") === true) {
    var multistate = 1;
  } else {
    var multistate = 0;
  }
  $.ajax({
    url: "/admin/multishare",
    method: "post",
    data: JSON.stringify({ files: selected, state: multistate}),
    contentType: "application/json;charset=utf-8",
    success: function (res) {
      popupoff();
      cancelselect();
      if (res == "OK") {
        Swal.fire({
          icon: 'success',
          title: 'Success',
          text: 'Change applied!',
        })
      }
    }
  });
}


// toggle options area and outside click to close
function toggleoptions() {
  $('.upload-options-area').toggleClass('upload-options-area--open');
}

$(document).mouseup(function (e) {
  var container = $(".upload-options-area");
  if (!container.is(e.target) && container.has(e.target).length === 0) {
    container.removeClass('upload-options-area--open');
  }
});
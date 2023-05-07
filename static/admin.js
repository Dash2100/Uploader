let uploading = 0;
let file_count = 0;
let uploaded_count = 0;
let sharebutton;
let linkbutton;
let linkstate;

function downloadFile(filename) {
  let url = '/admin/download/' + filename;
  let a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
};

function downloadURL(URL) {
  let a = document.createElement('a');
  a.href = URL;
  a.download = filename;
  a.click();
};

function $id(id) {
  return document.getElementById(id);
}

function init() {
  var domain = window.location.href.split('/')[2];
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

function hideall() {
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
  $id('rename').onclick = function () { rename(name); };
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

function downloadzip() {
  // post to /download/zip and save
  var data = JSON.stringify({ files: selected });
  $.ajax({
    url: "/admin/download/zip",
    method: "post",
    data: data,
    contentType: "application/json;charset=utf-8",
    xhrFields: {
      responseType: "blob" // set the response type to blob
    },
    success: function (blob) {
      var url = window.URL.createObjectURL(blob);
      var link = document.createElement("a");
      link.href = url;
      link.download = "download.zip";
      document.body.appendChild(link);
      link.click();

      // clean up the URL and link
      window.URL.revokeObjectURL(url);
      document.body.removeChild(link);
    }
  });
  cancelselect();
}



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

function func_button() {
  if (selecting == 0) {
    upload();
  } else {
    cancelselect();
  }
}

let selecting = 0;
function selectfile() {
  selecting = 1
  $('.modfile-icon').addClass('hide');
  $('.file-card').addClass('file-card-disable');
  $('.file').addClass('file-select');
  $('.opt-icons').addClass('hide');
  $('.file-list').addClass('file-list-editing');
  $('#ani-button').addClass('cancel-select');
}

let selected = [];
function cancelselect() {
  $('.modfile-icon').removeClass('hide');
  $('.file').removeClass('file-select');
  $('.file').removeClass('file-selected');
  $('.file-card').removeClass('file-card-disable');
  $('.file-card').removeClass('file-card-selected');
  $('.opt-icons').removeClass('hide');
  $('.edit-options').removeClass('edit-options-open');
  $('.file-list').removeClass('file-list-editing');
  $('#ani-button').removeClass('cancel-select');

  selecting = 0;
  selected = [];
}

function select(fileID) {
  if (selecting === 1) {

    let filename = $('#' + fileID + "-name").text();
    if (selected.includes(filename)) {
      selected.splice(selected.indexOf(filename), 1);
      multi_select_ui(fileID, 1);
    }
    else {
      selected.push(filename);
      multi_select_ui(fileID, 0);
    }
  }
  
}

function multi_select_ui(fileID, state) {
  if (selected.length > 0) {
    $('#edit-options-text').text(selected.length + " Files selected");
    $('.edit-options').addClass('edit-options-open');
  } else {
    $('.edit-options').removeClass('edit-options-open');
  }

  if (state === 1) {
    $("#" + fileID).removeClass('file-selected');
    $("#" + fileID + "-card").removeClass('file-card-selected');
    $("#" + fileID + "-card").addClass('file-card-disable');
  }
  else {
    $("#" + fileID).addClass('file-selected');
    $("#" + fileID + "-card").removeClass('file-card-disable');
    $("#" + fileID + "-card").addClass('file-card-selected');
  }
}

function multidelete() {
  Swal.fire({
    title: "Are you sure?",
    text: "You will delete " + selected.length + " files",
    icon: "warning",
    showCancelButton: true,
    confirmButtonColor: "#7e403e",
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

function multishare() {
  if ($('#multi-Share-check').is(":checked") === true) {
    var multistate = 1;
  } else {
    var multistate = 0;
  }
  $.ajax({
    url: "/admin/multishare",
    method: "post",
    data: JSON.stringify({ files: selected, state: multistate }),
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


//rename
function rename(file) {
  Swal.fire({
    title: 'Rename',
    text: "Enter a new name for " + file + ":",
    input: 'text',
    inputValue: file,
    inputAttributes: {
      autocapitalize: 'off',
      id: 'rename-input'
    },
    showCancelButton: true,
    confirmButtonText: 'Rename',
    showLoaderOnConfirm: true,
    didOpen: function () {
      const dotIndex = $('#rename-input').val().lastIndexOf('.')
      $('#rename-input')[0].setSelectionRange(0, dotIndex)
      $('#rename-input').focus()

    },
    preConfirm: (newname) => {
      if (newname == "") {
        Swal.showValidationMessage(
          `You must enter a name`
        )
      }
      else if (newname == file) {
        Swal.showValidationMessage(
          `You must enter a different name`
        )
      }
      else {
        return $.ajax({
          url: "/admin/rename",
          method: "post",
          data: JSON.stringify({ filename: file, newname: newname }),
          contentType: "application/json;charset=utf-8",
          success: function (res) {
            if (res == "OK") {
              location.reload();
            }
            if (res == "Already in use") {
              Swal.showValidationMessage(
                `This name already in use`
              )
            }
            if (res == "illegal") {
              Swal.showValidationMessage(
                `The name can't contain special characters or spaces`
              )
            }
          }
        });
      }
    }
  })
}

//preview

function checkPreviewable(filename) {
  let ext = filename.split('.').pop().toLowerCase();

  if (filename.indexOf('.') == -1) {
    return false;
  }

  if (!ext) {
    return false;
  }

  let image = ['bmp', 'gif', 'ico', 'jpeg', 'jpg', 'png', 'svg', 'tiff', 'webp'];
  let text = ['txt', 'md', 'log', 'csv', 'tsv', 'tab', 'json', 'xml', 'html', 'htm', 'css', 'js', 'jsx', 'php', 'rb', 'py', 'c', 'cpp', 'h', 'hpp', 'java', 'pl', 'sh', 'bat', 'ps1', 'sql', 'r', 'yaml', 'yml', 'ini', 'env'];

  if (ext == 'pdf') {
    return ext;
  }

  if (image.indexOf(ext) != -1) {
    return 'image';
  }

  if (text.indexOf(ext) != -1) {
    return 'text';
  }

  return false;
}

function preview(filename) {

  let filetype = checkPreviewable(filename);
  if (!filetype) {
    var link = `/admin/preview/${filename}`;
    var content =
      `<div class="preview-info">
          <a class="preview-notavailable">Preview not available</a>
          <button class="button preview-download" onclick="downloadFile('${filename}')">Download</button>
      </div>`;
  }

  if (filetype == 'pdf') {
    var link = `/pdfview?file=/admin/preview/${filename}`
    var content = `<iframe class="preview-iframe" src="${link}"></iframe>`;
  }

  if (filetype == 'image') {
    var link = `/admin/preview/${filename}`;
    var content = `<img class="preview-img" src="${link}">`;
  }

  if (filetype == 'text') {
    var link = `/admin/preview/${filename}`;
    var text = '';
    $.ajax({
      url: `/admin/preview/${filename}`,
      async: false,
      success: function (data) {
        text = data;
      }
    });

    var content = `<textarea readonly class="preview-text">${text}</textarea>`;
  }


  let template = $('#file-prev').text();
  template = template.replace('%filename%', filename);
  template = template.replace('%preview-content%', content);
  template = template.replace('%preview-link%', link);

  template = $(template);

  //disable scroll
  $('body').css('overflow', 'hidden');

  $('#preview-area').append(template);

  //for animation
  setTimeout(function () {
    template.addClass('popup--opened');
  }, 1);
}

function previewoff() {
  //enable scroll
  $('body').css('overflow', 'auto');

  $('#preview').removeClass('popup--opened');
  setTimeout(function () {
    $('#preview').remove();
  }, 200);
}
let file_count = 0;
let uploaded_count = 0;
let sharebutton;
let linkbutton;
let linkstate;

let isLoaded = false;
let page = 1;

let files_list = {}; // filename -> uuid
let files_names = {}; // uuid -> filename

document.addEventListener('DOMContentLoaded', function () {
    let domain = window.location.href.split('/')[2];
    $('#baseurl').text(domain + ' /');

    // 初始隱藏 placeholder
    $('.file-placeholder').hide();

    getFileList();

    $('.modfile-icon').click(function (e) {
        e.stopPropagation(); // 防止事件冒泡到.file
        let fileName = $(this).closest('.file').data('file-name'); // 使用.closest()找到最近的.file父元素
        modify(fileName);
    });

    $('#file-list-area').on('scroll', function () {
        let $this = $(this);
        if (!isLoading && $this.scrollTop() + $this.innerHeight() >= $this[0].scrollHeight - 100) {
            isLoading = true; // 標記正在加載中
            // 顯示 loading placeholder
            $('.file-placeholder').show();
            getFileList(page);
        }
    });

    $(document).keyup(function (event) {
        if (event.which === 27) {
            previewoff();
            popupoff();
            searchclose();
            cancelselect();
        }
    });

});

function getFileList(reqPage) {
    let data = JSON.stringify({
        "page": reqPage,
        "admin_mode": true
    });

    $.ajax({
        url: "/files/list",
        method: "post",
        contentType: "application/json;charset=utf-8",
        data: data,
        success: function (filesList) {
            // 隱藏 loading placeholder
            $('.file-placeholder').hide();

            if (filesList.length === 0) {
                $('#file-list-area').off('scroll');
                isLoading = false;
                return;
            }

            filesList.forEach(fileData => {
                let template = $('#file-block-template').text()
                    .replace('%file-name%', fileData.name)
                    .replace('%file-date%', fileData.date)
                    .replace('%file-size%', fileData.size)
                    .replace('%file-downloads%', fileData.downloads)

                template = $(template);
                template.prop('id', fileData.uuid);

                template.find('.file-card').click(function (e) {
                    preview(fileData.uuid); // 改為傳入UUID
                });

                $('#file-list').append(template);
                files_list[fileData.name] = fileData.uuid;
                files_names[fileData.uuid] = fileData.name;

                template.click(function () {
                    select(fileData.uuid);
                });
            });

            page++;
            isLoading = false;
        },
        error: function () {
            // 發生錯誤時也要隱藏 loading placeholder
            $('.file-placeholder').hide();
            isLoading = false;
        }
    });
}

function downloadFile(filename) {
    let file_uuid = files_list[filename];

    let url = '/files/download?file=' + file_uuid;
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

// popup
function upload() {
    hideall();
    $('#upload-area').show();
    var x = document.getElementsByClassName("popup")[0];
    x.classList.add("popup--opened");
}

function popupoff() {
    var x = document.getElementsByClassName("popup")[0];
    x.classList.remove("popup--opened");

    $('#savechange').off('click');
    $('#delfile').off('click');
    $('#rename').off('click');
}

function hideall() {
    $('#modfile-area').hide();
    $('#upload-area').hide();
    $('#multi-modfile-area').hide();
}

function modify(uuid) {
    sharebutton = 0;
    linkbutton = 0;
    linkstate = 0;
    hideall();
    filestate(uuid);
    $('#link-input').hide();
    $('#modfile-area').show();
    $('#savechange').on('click', function () { save(uuid); });
    $('#delfile').on('click', function () { delFile(uuid); });
    $('#rename').on('click', function () { rename(uuid); });
    $('#modfile-name').html(files_names[uuid]);
    var x = document.getElementsByClassName("popup")[0];
    x.classList.add("popup--opened");
}

function multimodify() {
    hideall();
    $('#multi-modfile-area').show();
    $('#multi-Share-check').prop('checked', false);
    $('#multi-modfile-name').html(selected.length + " Files");
    var x = document.getElementsByClassName("popup")[0];
    x.classList.add("popup--opened");
}

function downloadzip() {
    selecting = 0;
    $('#xbtn').prop('disabled', true);
    $('#edit-options-text').text("Preparing Download...");
    $('#download-btn-text').hide();
    $('#download-btn-loading').show();
    $('#downloadzip-btn').prop('disabled', true);
    $('#multimodify-btn').addClass('select-edit-hide');
    // post to /admin/download_zip and save
    var data = JSON.stringify({ files: selected });
    $.ajax({
        url: "/files/download_zip",
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
    }).then(function () {
        cancelselect();
        setTimeout(function () {
            $('#xbtn').prop('disabled', false);
            $('#download-btn-text').show();
            $('#download-btn-loading').hide();
            $('#downloadzip-btn').prop('disabled', false);
            $('#multimodify-btn').removeClass('select-edit-hide');
        }, 280);
    });
}

function delFile(uuid) {
    Swal.fire({
        title: 'Delete?',
        text: "You won't be able to revert this!",
        // icon: 'question',
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
                data: JSON.stringify({ uuid: uuid }),
                contentType: "application/json;charset=utf-8",
                success: function (res) {
                    if (res === "OK") {
                        location.reload();
                    }
                },
                error: function (res) {
                    Swal.fire({
                        title: "Error",
                        text: "Something went wrong, please try again later.",
                        // icon: "error",
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

// UI

function add_file(id, file) {
    file_count++;
    var template = $('#uploading-file-template').text();
    template = template.replace('%filename%', file.name);
    template = $(template);
    template.prop('id', 'file-' + id);

    $('#uploading-list').append(template[0]);
}

function file_progress(id, percent) {
    var file = $('#file-' + id);
    var progress = file.find('#progressbar');
    var percent_text = file.find('#percent_text');
    progress.css('width', percent + '%');
    percent_text.text(percent + '%');
    if (percent === 100) {
        progress.css('backgroundColor', '#546ad8');
    }
}

function filestate(uuid) {
    $.ajax({
        url: "/admin/filestate",
        method: "post",
        contentType: "application/json;charset=utf-8",
        data: JSON.stringify({ uuid: uuid }),
        success: function (res) {
            var res = JSON.parse(res);
            sharebutton = res.share;
            linkstate = res.link;
            console.log(linkstate);
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

function save(uuid) {
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
            data: JSON.stringify({ uuid: uuid, state: sstate }),
            contentType: "application/json;charset=utf-8",
            success: function (res) {
                if (res === "OK") {
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
                data: JSON.stringify({ shortlink: shortlink, uuid: uuid }),
                contentType: "application/json;charset=utf-8",
                success: function (res) {
                    if (res === "OK") {
                        popupoff();
                    }
                    if (res === "Already in use") {
                        Swal.fire({
                            icon: 'error',
                            title: 'Oops...',
                            text: 'This shortlink already in use!',
                        })
                    }
                    if (res === "Empty") {
                        Swal.fire({
                            icon: 'error',
                            title: 'Oops...',
                            text: 'You must enter a shortlink!',
                        })
                    }
                    if (res === "illegal") {
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
            data: JSON.stringify({ uuid: uuid }),
            contentType: "application/json;charset=utf-8",
            success: function (res) {
                if (res === "OK") {
                    popupoff();
                }
            }
        });
    }
}

let selecting = 0;
let functioning = 0;
function selectfile() {
    selecting = 1;
    functioning = 1;
    topiconhide();
    // 隱藏 loading placeholders
    $('.file-placeholder').hide();
    $('.edit-options').show();
    $('.modfile-icon').addClass('hide');
    $('.file-card').addClass('file-card-disable');
    $('.file').addClass('file-select');
    $('.file-list').addClass('file-list-editing');
}

let selected = [];
function cancelselect() {
    $('.modfile-icon').removeClass('hide');
    $('.file').removeClass('file-select');
    $('.file').removeClass('file-selected');
    $('.file-card').removeClass('file-card-disable');
    $('.file-card').removeClass('file-card-selected');
    $('.edit-options').removeClass('edit-options-open');
    $('.file-list').removeClass('file-list-editing');
    topiconshow();

    selecting = 0;
    functioning = 0;
    selected = [];

    setTimeout(function () {
        $('.edit-options').hide();
    }, 280);
}

function topiconhide() {
    $('#ani-button').addClass('cancel-select');
    $('.opt-icons').addClass('hide');
}

function topiconshow() {
    $('#ani-button').removeClass('cancel-select');
    $('.opt-icons').removeClass('hide');
}

function func_button() {
    if (functioning === 0) {
        upload();
    } else {
        cancelselect();
        searchclose();
    }
}

function select(uuid) {
    if (selecting === 1) {

        let fileObj = $($('#' + uuid).html());
        let filename = fileObj.find('.file-name').text();

        if (selected.includes(uuid)) {
            selected.splice(selected.indexOf(uuid), 1);
            multi_select_ui(uuid, 1);
        }
        else {
            selected.push(uuid);
            multi_select_ui(uuid, 0);
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
        // icon: "warning",
        showCancelButton: true,
        confirmButtonColor: "#7e403e",
        confirmButtonText: "Delete",
        allowEnterKey: false,
    }).then((result) => {
        if (result.isConfirmed) {
            $.ajax({
                url: "/files/multidelete",
                method: "post",
                data: JSON.stringify({ uuids: selected }),
                contentType: "application/json;charset=utf-8",
                success: function (res) {
                    if (res === "OK") {
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
        data: JSON.stringify({ uuids: selected, state: multistate }),
        contentType: "application/json;charset=utf-8",
        success: function (res) {
            popupoff();
            cancelselect();
            if (res === "OK") {
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
function rename(uuid) {
    let filename = files_names[uuid];
    Swal.fire({
        title: 'Rename',
        text: "Enter a new name for " + filename + ":",
        input: 'text',
        inputValue: filename,
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
            if (newname === "") {
                Swal.showValidationMessage(
                    `You must enter a name`
                )
            }
            else if (newname === filename) {
                Swal.showValidationMessage(
                    `You must enter a different name`
                )
            }
            else if (!/^[\p{L}\p{N}\-._\s]+$/u.test(newname)) {
                Swal.showValidationMessage(
                    `The name can't contain special characters`
                )
            }
            else {
                return $.ajax({
                    url: "/admin/rename",
                    method: "post",
                    data: JSON.stringify({ uuid: uuid, newname: newname }),
                    contentType: "application/json;charset=utf-8",
                    success: function (res) {
                        if (res === "OK") {
                            location.reload();
                        }
                        if (res === "Already in use") {
                            Swal.showValidationMessage(
                                `This name already in use`
                            )
                        }
                        if (res === "illegal") {
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

    if (filename.indexOf('.') === -1) {
        return false;
    }

    if (!ext) {
        return false;
    }

    let image = ['bmp', 'gif', 'ico', 'jpeg', 'jpg', 'png', 'svg', 'tiff', 'webp'];
    let text = ['txt', 'md', 'log', 'csv', 'tsv', 'tab', 'json', 'xml', 'html', 'htm', 'css', 'js', 'jsx', 'php', 'rb', 'py', 'c', 'cpp', 'h', 'hpp', 'java', 'pl', 'sh', 'bat', 'ps1', 'sql', 'r', 'yaml', 'yml', 'ini', 'env', 'cmd', 'ino'];

    if (ext === 'pdf') {
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

function preview(uuid) {
    let filename = files_names[uuid]; // 取得檔名用於顯示
    let filetype = checkPreviewable(filename);

    if (!filetype) {
        var link = `/preview/${uuid}`;
        var content =
            `<div class="preview-info">
                    <a class="preview-notavailable">Preview not available</a>
                    <button class="button preview-download" onclick="downloadFile('${filename}')">Download</button>
            </div>`;
    }

    if (filetype === 'pdf') {
        var link = `/pdf_viewer?file=/preview/${uuid}`
        var content = `<iframe class="preview-iframe" src="${link}"></iframe>`;
    }

    if (filetype === 'image') {
        var link = `/preview/${uuid}`;
        var content = `<img class="preview-img" src="${link}">`;
    }

    if (filetype === 'text') {
        var link = `/preview/${uuid}`;
        var text = '';
        $.ajax({
            url: `/preview/${uuid}`,
            async: false,
            CORS: true,
            success: function (data) {
                text = data;
            }
        });

        var content = `<textarea readonly class="preview-text">${text}</textarea>`;
    }

    let template = $('#file-preview-template').text();
    template = template.replace('%filename%', filename); // 顯示用還是用檔名
    template = template.replace('%preview-content%', content);
    template = template.replace('%preview-link%', link);

    template = $(template);

    //disable scroll
    $('body').css('overflow', 'hidden');

    $('#preview-area').append(template);

    //for animation
    setTimeout(function () {
        template.addClass('popup--opened');
    }, .1);
}

function previewoff() {
    //enable scroll
    $('body').css('overflow', 'auto');

    $('#preview').removeClass('popup--opened');
    setTimeout(function () {
        $('#preview').remove();
    }, 170);
}

function searchopen() {
    topiconhide();
    functioning = 1;
    $('#search').addClass('search-open');
    $('#file-list').addClass('file-list-out');
    $('#search-input').focus();
    $('.opt-icons').addClass('hide');
    $('#xbtn').removeClass('top-icon-hide');
}

function searchclose() {
    $('#search').removeClass('search-open');
    $('#file-list').removeClass('file-list-out');
    $('#search-input').val('');
    $('.file').show();
    $('.no-files').hide();
    $('#clstext').removeClass('clstext-show');
    topiconshow();
}

function clearsearchtext() {
    $('#search-input').val('');
    $('#clstext').removeClass('clstext-show');
    $('.file').show();
    $('.no-files').hide();
}

function search(searchString) {
    const keys = Object.keys(files_list);
    const filteredKeys = keys.filter(key => key.toLowerCase().includes(searchString));
    const result = [];
    filteredKeys.forEach(key => {
        result.push(files_list[key]);
    }
    );

    $('.file').hide();

    if (result.length === 0) {
        $('.no-files').show();
    }
    else {
        $('.no-files').hide();
        result.forEach(file => {
            $('#' + file).show();
        }
        );
    }

}

$(document).ready(function () {
    $('#search-input').on('input', function (event) {
        var inputValue = $(this).val().toLowerCase();
        search(inputValue);
        if (inputValue.length > 0) {
            $('#clstext').addClass('clstext-show');
        }
        else {
            $('#clstext').removeClass('clstext-show');
        }
    });
});
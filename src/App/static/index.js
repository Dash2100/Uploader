let isLoading = false;
let hasMore = true;
let page = 1;

let files_list = {}; // filename -> uuid
let files_names = {}; // uuid -> filename

function showPlaceholders() {
    $('.file-placeholder').addClass('is-loading');
}

function hidePlaceholders() {
    $('.file-placeholder').removeClass('is-loading');
}

document.addEventListener('DOMContentLoaded', function () {
    hidePlaceholders();
    getFileList({ silent: true });

    $('#file-list-area').on('scroll', function () {
        let $this = $(this);
        let nearBottom = $this.scrollTop() + $this.innerHeight() >= $this[0].scrollHeight - 100;
        if (!isLoading && hasMore && nearBottom) {
            getFileList({ silent: false });
        }
    });

    $(document).keyup(function (event) {
        if (event.which === 27) {
            previewoff();
            searchclose();
            cancelselect();
        }
    });
});

function appendFileRow(fileData) {
    let template = $('#file-block-template').text()
        .replace('%file-name%', fileData.name)
        .replace('%file-date%', fileData.date)
        .replace('%file-size%', fileData.size)
        .replace('%file-downloads%', fileData.downloads);

    template = $(template);
    template.prop('id', fileData.uuid);

    template.find('.file-card').on('click', function () {
        if (selecting !== 1) {
            preview(fileData.uuid);
        }
    });

    template.on('click', function () {
        if (selecting === 1) {
            select(fileData.uuid);
        }
    });

    $('#file-list').append(template);
    files_list[fileData.name] = fileData.uuid;
    files_names[fileData.uuid] = fileData.name;
}

function getFileList(opts) {
    opts = opts || {};
    isLoading = true;
    if (!opts.silent) showPlaceholders();

    $.ajax({
        url: "/files/list",
        method: "post",
        contentType: "application/json;charset=utf-8",
        data: JSON.stringify({ page: page, admin_mode: false }),
        success: function (filesList) {
            hidePlaceholders();
            if (!filesList || filesList.length === 0) {
                hasMore = false;
                isLoading = false;
                if (page === 1) $('.no-files').addClass('is-visible');
                return;
            }
            $('.no-files').removeClass('is-visible');
            filesList.forEach(appendFileRow);
            page++;
            isLoading = false;
        },
        error: function () {
            hidePlaceholders();
            isLoading = false;
        }
    });
}

function downloadFile(uuid) {
    let filename = files_names[uuid] || '';
    let a = document.createElement('a');
    a.href = '/files/download?file=' + uuid;
    a.download = filename;
    a.click();
}

function downloadzip() {
    selecting = 0;
    $('#xbtn').prop('disabled', true);
    $('#edit-options-text').text("Preparing Download...");
    $('#download-btn-text').hide();
    $('#download-btn-loading').show();
    $('#downloadzip-btn').prop('disabled', true);

    let data = JSON.stringify({ files: selected });
    $.ajax({
        url: "/files/download_zip",
        method: "post",
        data: data,
        contentType: "application/json;charset=utf-8",
        xhrFields: { responseType: "blob" },
        success: function (blob) {
            let url = window.URL.createObjectURL(blob);
            let link = document.createElement("a");
            link.href = url;
            link.download = "download.zip";
            document.body.appendChild(link);
            link.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(link);
        }
    }).then(function () {
        $('#xbtn').prop('disabled', false);
        $('#download-btn-text').show();
        $('#download-btn-loading').hide();
        $('#downloadzip-btn').prop('disabled', false);
        cancelselect();
    });
}

function checkPreviewable(filename) {
    if (!filename || filename.indexOf('.') === -1) return false;
    let ext = filename.split('.').pop().toLowerCase();
    if (!ext) return false;

    let image = ['bmp', 'gif', 'ico', 'jpeg', 'jpg', 'png', 'svg', 'tiff', 'webp'];
    let text = ['txt', 'md', 'log', 'csv', 'tsv', 'tab', 'json', 'xml', 'html', 'htm', 'css', 'js', 'jsx', 'php', 'rb', 'py', 'c', 'cpp', 'h', 'hpp', 'java', 'pl', 'sh', 'bat', 'ps1', 'sql', 'r', 'yaml', 'yml', 'ini', 'env', 'cmd', 'ino'];

    if (ext === 'pdf') return 'pdf';
    if (image.indexOf(ext) !== -1) return 'image';
    if (text.indexOf(ext) !== -1) return 'text';
    return false;
}

function preview(uuid) {
    let filename = files_names[uuid] || '';
    let filetype = checkPreviewable(filename);
    let link, content;

    if (!filetype) {
        link = `/preview/${uuid}`;
        content =
            `<div class="preview-info">
                <a class="preview-notavailable">Preview not available</a>
                <button class="button preview-download" onclick="downloadFile('${uuid}')">Download</button>
            </div>`;
    } else if (filetype === 'pdf') {
        link = `/preview/pdf_viewer?file=/preview/${uuid}`;
        content = `<iframe class="preview-iframe" src="${link}"></iframe>`;
    } else if (filetype === 'image') {
        link = `/preview/${uuid}`;
        content = `<img class="preview-img" src="${link}">`;
    } else if (filetype === 'text') {
        link = `/preview/${uuid}`;
        let text = '';
        $.ajax({
            url: link,
            async: false,
            success: function (data) { text = data; }
        });
        content = `<textarea readonly class="preview-text">${text}</textarea>`;
    }

    let template = $('#file-preview-template').text();
    template = template.replace('%uuid%', uuid);
    template = template.replace('%preview-content%', content);
    template = template.replace('%preview-link%', link);

    template = $(template);

    $('body').css('overflow', 'hidden');
    $('#preview-area').append(template);

    setTimeout(function () {
        template.addClass('popup--opened');
    }, 1);
}

function previewoff() {
    $('body').css('overflow', 'auto');
    $('#preview').removeClass('popup--opened');
    setTimeout(function () {
        $('#preview').remove();
    }, 200);
}

let selecting = 0;
function selectfile() {
    selecting = 1;
    hidePlaceholders();
    $('.edit-options').show();
    $('.file-card').addClass('file-card-disable');
    $('.file-list').addClass('file-list-editing');
    $('.file').addClass('file-select');
    $('.opt-icons').addClass('hide');
    $('#loginbtn').addClass('top-icon-hide');
    $('#xbtn').removeClass('top-icon-hide');
}

let selected = [];
function cancelselect() {
    $('.file').removeClass('file-select');
    $('.file-card').removeClass('file-card-disable');
    $('.file-list').removeClass('file-list-editing');
    $('.file').removeClass('file-selected');
    $('.file-card').removeClass('file-card-selected');
    $('.opt-icons').removeClass('hide');
    $('#loginbtn').removeClass('top-icon-hide');
    $('#xbtn').addClass('top-icon-hide');
    $('.edit-options').removeClass('edit-options-open');

    selecting = 0;
    selected = [];

    setTimeout(function () {
        $('.edit-options').hide();
    }, 280);
}

function select(uuid) {
    if (selecting !== 1) return;
    if (selected.includes(uuid)) {
        selected.splice(selected.indexOf(uuid), 1);
        multi_select_ui(uuid, 1);
    } else {
        selected.push(uuid);
        multi_select_ui(uuid, 0);
    }
}

function multi_select_ui(uuid, state) {
    if (selected.length > 0) {
        $('#edit-options-text').text(selected.length + " Files selected");
        $('.edit-options').addClass('edit-options-open');
    } else {
        $('.edit-options').removeClass('edit-options-open');
    }

    let $file = $(document.getElementById(uuid));
    let $card = $file.find('.file-card');
    if (state === 1) {
        $file.removeClass('file-selected');
        $card.removeClass('file-card-selected').addClass('file-card-disable');
    } else {
        $file.addClass('file-selected');
        $card.removeClass('file-card-disable').addClass('file-card-selected');
    }
}

function searchopen() {
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
    $('.no-files').removeClass('is-visible');
    $('#clstext').removeClass('clstext-show');
}

function clearsearchtext() {
    $('#search-input').val('');
    $('#clstext').removeClass('clstext-show');
    $('.file').show();
    $('.no-files').removeClass('is-visible');
}

function search(searchString) {
    const keys = Object.keys(files_list);
    const filteredKeys = keys.filter(key => key.toLowerCase().includes(searchString));
    const result = filteredKeys.map(key => files_list[key]);

    $('.file').hide();
    if (result.length === 0) {
        $('.no-files').addClass('is-visible');
    } else {
        $('.no-files').removeClass('is-visible');
        result.forEach(uuid => {
            $(document.getElementById(uuid)).show();
        });
    }
}

$(document).ready(function () {
    $('#search-input').on('input', function () {
        let inputValue = $(this).val().toLowerCase();
        search(inputValue);
        if (inputValue.length > 0) {
            $('#clstext').addClass('clstext-show');
        } else {
            $('#clstext').removeClass('clstext-show');
        }
    });
});

let files_list = {};

document.addEventListener('DOMContentLoaded', function () {
    $(document).keyup(function (event) {
        if (event.which === 27) {
            previewoff();
            searchclose();
            cancelselect();
        }
    });
});

function downloadFile(filename) {
    let url = '/download/' + filename;
    let a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
};


function downloadzip() {
    selecting = 0;
    $('#xbtn').prop('disabled', true);
    $('#edit-options-text').text("Preparing Download...");
    $('#download-btn-text').hide();
    $('#download-btn-loading').show();
    $('#downloadzip-btn').prop('disabled', true);
    // post to /download/zip and save
    var data = JSON.stringify({ files: selected });
    $.ajax({
        url: "/download/zip",
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
        $('#xbtn').prop('disabled', false);
        $('#download-btn-text').show();
        $('#download-btn-loading').hide();
        $('#downloadzip-btn').prop('disabled', false);
        cancelselect();
    });
}

function checkPreviewable(filename) {
    let ext = filename.split('.').pop().toLowerCase();

    if (filename.indexOf('.') == -1) {
        return false;
    }

    if (!ext) {
        return false;
    }

    let image = ['bmp', 'gif', 'ico', 'jpeg', 'jpg', 'png', 'svg', 'tiff', 'webp'];
    let text = ['txt', 'md', 'log', 'csv', 'tsv', 'tab', 'json', 'xml', 'html', 'htm', 'css', 'js', 'jsx', 'php', 'rb', 'py', 'c', 'cpp', 'h', 'hpp', 'java', 'pl', 'sh', 'bat', 'ps1', 'sql', 'r', 'yaml', 'yml', 'ini', 'env', 'cmd'];

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
        var link = `/preview/${filename}`;
        var content =
            `<div class="preview-info">
            <a class="preview-notavailable">Preview not available</a>
            <button class="button preview-download" onclick="downloadFile('${filename}')">Download</button>
        </div>`;
    }

    if (filetype == 'pdf') {
        var link = `/pdfview?file=/preview/${filename}`
        var content = `<iframe class="preview-iframe" src="${link}"></iframe>`;
    }

    if (filetype == 'image') {
        var link = `/preview/${filename}`;
        var content = `<img class="preview-img" src="${link}">`;
    }

    if (filetype == 'text') {
        var link = `/preview/${filename}`;
        var text = '';
        $.ajax({
            url: `/preview/${filename}`,
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

let selecting = 0;
function selectfile() {
    selecting = 1
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

function select(fileID) {
    if (selecting === 1) {
        let filename = $('#' + fileID + "-name").text();
        console.log(filename);
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
    $('.no-files').hide();
    $('#clstext').removeClass('clstext-show');
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

    if (result.length == 0) {
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

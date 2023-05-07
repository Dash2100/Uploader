function downloadFile(filename) {
    let url = '/download/' + filename;
    let a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
};

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
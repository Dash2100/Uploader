function downloadFile(fileName) {
    let url = '/download/' + fileName;
    let a = document.createElement('a');
    a.href = url;
    a.download = fileName;
    a.click();
};

function checkPreviewable(filename) {
    let ext = filename.split('.').pop().toLowerCase();

    if (filename.indexOf('.') == -1) {
        return false;
    }

    if(!ext) {
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
    if(!filetype){
        alert("not support")
        return;
    }

    if(filetype == 'pdf'){
        var content = `<iframe class="preview-iframe" src="/pdfview?file=/download/${filename}"></iframe>`;
    }

    if(filetype == 'image'){
        var content = `<img class="preview-img" src="/download/${filename}">`;
    }

    let template = $('#file-prev').text();
    template = template.replace('%preview-content%', content);
    console.log(template);
    template = $(template);
  
    //disable scroll
    $('body').css('overflow', 'hidden');

    $('#preview-area').append(template);
    // wait 0.5 sec for animation
    setTimeout(function() {
        template.addClass('popup--opened');
    }
    , 1);
}

function popupoff(){

    //enable scroll
    $('body').css('overflow', 'auto');

    $('#preview').removeClass('popup--opened');
    setTimeout(function() {
        $('#preview').remove();
    }
    , 200);
}
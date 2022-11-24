function downloadFile(fileName) {
    let url = '/download/' + fileName;
    let a = document.createElement('a');
    a.href = url;
    a.download = fileName;
    a.click();
};
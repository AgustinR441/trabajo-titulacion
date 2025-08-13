const uploadedFiles = [];
const dropArea = document.querySelector('.drop-section')
const listSection = document.querySelector('.list-section')
const listContainer = document.querySelector('.list')
const fileSelector = document.querySelector('.file-selector')
const fileSelectorInput = document.querySelector('.file-selector-input')

// subir archivos con el boton de buscar
fileSelector.onclick = () => fileSelectorInput.click()
fileSelectorInput.onchange = () => {
    [...fileSelectorInput.files].forEach((file) => {
        if(typeValidation(file.type)){
            console.log(file)
            uploadFile(file)
        }
    })
}

// archivo sobre el drag area
dropArea.ondragover = (e) => {
    e.preventDefault();
    [...e.dataTransfer.items].forEach((item) => {
        if(typeValidation(item.type)){
            dropArea.classList.add('drag-over-effect')
        }
    })
}
// cuando el archivo sale del drag area
dropArea.ondragleave = () => {
    dropArea.classList.remove('drag-over-effect')
}
// soltar el archivo en el drag area
dropArea.ondrop = (e) => {
    e.preventDefault();
    dropArea.classList.remove('drag-over-effect')
    if(e.dataTransfer.items){
        [...e.dataTransfer.items].forEach((item) => {
            if(item.kind === 'file'){
                const file = item.getAsFile();
                if(typeValidation(file.type)){
                    uploadFile(file)
                }
            }
        })
    }else{
        [...e.dataTransfer.files].forEach((file) => {
            if(typeValidation(file.type)){
                uploadFile(file)
            }
        })
    }
}


// tipo de archivos permitidos
function typeValidation(type) {
    return [
      'audio/flac',
      'audio/m4a',
      'audio/mp3',
      'audio/mp4',
      'audio/mpeg',
      'audio/mpga',
      'audio/oga',
      'audio/ogg',
      'audio/wav',
      'audio/webm',
      'video/mp4',
      'video/webm'
    ].includes(type);
  }

// subir
function uploadFile(file){
    listSection.style.display = 'block'
    var li = document.createElement('li')
    li.classList.add('in-prog')
    li.innerHTML = `
        <div class="col">
            <img src="/static/assets/images/uploader/image.png" alt="">
        </div>
        <div class="col">
            <div class="file-name">
                <div class="name">${file.name}</div>
                <span>0%</span>
            </div>
            <div class="file-progress">
                <span></span>
            </div>
            <div class="file-size">${(file.size/(1024*1024)).toFixed(2)} MB</div>
        </div>
        <div class="col">
            <svg xmlns="http://www.w3.org/2000/svg" class="cross" height="20" width="20"><path d="m5.979 14.917-.854-.896 4-4.021-4-4.062.854-.896 4.042 4.062 4-4.062.854.896-4 4.062 4 4.021-.854.896-4-4.063Z"/></svg>
            <svg xmlns="http://www.w3.org/2000/svg" class="tick" height="20" width="20"><path d="m8.229 14.438-3.896-3.917 1.438-1.438 2.458 2.459 6-6L15.667 7Z"/></svg>
        </div>
    `
    listContainer.prepend(li)
    var http = new XMLHttpRequest()
    var data = new FormData()
    data.append('file', file)
    http.onload = () => {
        li.classList.add('complete')
        li.classList.remove('in-prog')
    }
    http.upload.onprogress = (e) => {
        var percent_complete = (e.loaded / e.total)*100
        li.querySelectorAll('span')[0].innerHTML = Math.round(percent_complete) + '%'
        li.querySelectorAll('span')[1].style.width = percent_complete + '%'
    }
    http.open('POST', '/upload', true)
    http.upload.onprogress = (e) => {
        const pct = Math.round((e.loaded / e.total) * 100)
        li.querySelectorAll('span')[0].textContent = pct + '%'
        li.querySelector('.file-progress span').style.width = pct + '%'
    }
    http.onload = () => {
        li.classList.remove('in-prog')
        li.classList.add('complete')
        uploadedFiles.push(file.name)
    }
    http.onerror = () => {
        li.remove()
        alert('Error al subir ' + file.name)
    }
    http.send(data);


    li.querySelector('.cross').onclick = () => http.abort()
    http.onabort = () => li.remove()
}
// icono dependiendo del tipo de archivo
function iconSelector(type){
    var splitType = (type.split('/')[0] == 'application') ? type.split('/')[1] : type.split('/')[0];
    return splitType + '.png'
}

window.uploadedFiles = uploadedFiles;
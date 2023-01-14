
window.onload = function(){

    const phobert = document.getElementById('phobert')
    const phobert_content = document.getElementById('phobert-content')
    const roberta = document.getElementById('roberta')
    const roberta_content = document.getElementById('roberta-content')
    const cnn = document.getElementById('cnn')
    const cnn_content = document.getElementById('cnn-content')
    phobert.addEventListener('click',function(){
        phobert.classList.add('active')
        roberta.classList.remove('active')
        cnn.classList.remove('active')
        phobert_content.style.display=""
        roberta_content.style.display="none"
        cnn_content.style.display="none"
    })
    roberta.addEventListener('click',function(){
        roberta.classList.add('active')
        cnn.classList.remove('active')
        phobert.classList.remove('active')
        roberta_content.style.display=""
        phobert_content.style.display="none"
        cnn_content.style.display="none"
    })
    cnn.addEventListener('click',function(){
        cnn.classList.add('active')
        phobert.classList.remove('active')
        roberta.classList.remove('active')
        cnn_content.style.display=""
        phobert_content.style.display="none"
        roberta_content.style.display="none"
    })
}

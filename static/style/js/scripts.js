
window.onload = function(){

    const tf = document.getElementById('tf')
    const tf_content = document.getElementById('tf-content')
    const rnn = document.getElementById('rnn')
    const rnn_content = document.getElementById('rnn-content')
    const cnn = document.getElementById('cnn')
    const cnn_content = document.getElementById('cnn-content')
    tf.addEventListener('click',function(){
        tf.classList.add('active')
        rnn.classList.remove('active')
        cnn.classList.remove('active')
        tf_content.style.display=""
        rnn_content.style.display="none"
        cnn_content.style.display="none"
    })
    rnn.addEventListener('click',function(){
        rnn.classList.add('active')
        cnn.classList.remove('active')
        tf.classList.remove('active')
        rnn_content.style.display=""
        tf_content.style.display="none"
        cnn_content.style.display="none"
    })
    cnn.addEventListener('click',function(){
        cnn.classList.add('active')
        tf.classList.remove('active')
        rnn.classList.remove('active')
        cnn_content.style.display=""
        tf_content.style.display="none"
        rnn_content.style.display="none"
    })
}

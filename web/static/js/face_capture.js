const video = document.getElementById('webcam-video');
const canvas = document.getElementById('webcam-canvas');
const captureButton = document.getElementById('capture-button');
const statusDiv = document.getElementById('status-message');

async function setupWebcam(){
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        video.srcObject = stream; 
        video.play();
        console.log('Webcam initialisée avec succès');
    } catch (error) {
        console.error('Error accessing webcam:', error);
        statusDiv.textContent = 'Erreur : accès à la webcam refusé. ' + error.message;
    }
}

function captureImage() {
    const context = canvas.getContext('2d');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    return new Promise(resolve => {
        canvas.toBlob(resolve, 'image/jpeg', 0.95);
    });
}

async function sendImage(imageData) {
    statusDiv.textContent = "Envoi de l'image...";
    const form = new FormData();
    form.append('image', imageData, 'webcam_capture.jpg');

    try {
        const response = await fetch(window.location.href, {
            method: 'POST',
            body: form,
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        });

        if (response.status === 404) {
            statusDiv.textContent = 'Aucun visage enregistré. Veuillez d\'abord configurer votre authentification faciale.';
            statusDiv.classList.add('text-red-500');
            statusDiv.classList.remove('text-green-500');
            return;
        }

        const result = await response.json();
        if (result.status === 'success') {
            statusDiv.textContent = 'Vérification réussie !';
            statusDiv.classList.add('text-green-500');
            statusDiv.classList.remove('text-red-500');
            // Redirection après succès
            window.location.href = result.redirect || '/';
        } else  {
            statusDiv.textContent = `Échec de la vérification: ${result.message || 'Erreur inconnue'}`;
            statusDiv.classList.add('text-red-500');
            statusDiv.classList.remove('text-green-500');
        }
    } catch (error) {
        console.error('Erreur : ' + error.message);
        statusDiv.textContent = 'Erreur réseau : ' + error.message;
        statusDiv.classList.add('text-red-500');
        statusDiv.classList.remove('text-green-500');
    }
}

captureButton.addEventListener('click', async () => {
    const imageData = await captureImage();
    sendImage(imageData);
});

window.addEventListener('load', setupWebcam);
// ==========================================
// VOTE PAGE JAVASCRIPT
// ==========================================

let cameraStream = null;
let photoCaptured = false;


// ==========================================
// PAGE LOAD
// ==========================================

document.addEventListener("DOMContentLoaded", function () {

    console.log("voto.js loaded successfully");

    startCamera();

    updateSubmitButton();

});


// ==========================================
// CANDIDATE SELECTION
// ==========================================

function selectCandidate(element) {

    // Remove selection from all candidates
    const candidates = document.querySelectorAll(".candidate");

    candidates.forEach(function (candidate) {
        candidate.classList.remove("selected");
    });

    // Select current candidate
    element.classList.add("selected");

    // Find radio button
    const radio = element.querySelector(
        'input[type="radio"]'
    );

    if (radio) {
        radio.checked = true;
    }

    console.log(
        "Candidate selected:",
        radio ? radio.value : "none"
    );

    updateSubmitButton();
}


// ==========================================
// START CAMERA
// ==========================================

async function startCamera() {

    const video = document.getElementById("camera");
    const status = document.getElementById("cameraStatus");
    const captureBtn = document.getElementById("captureBtn");

    if (!video) {
        console.error("Camera video element not found");
        return;
    }

    if (!navigator.mediaDevices ||
        !navigator.mediaDevices.getUserMedia) {

        status.textContent =
            "Camera is not supported by this browser.";

        status.classList.add("error");

        captureBtn.disabled = true;

        return;
    }

    try {

        cameraStream =
            await navigator.mediaDevices.getUserMedia({

                video: {
                    facingMode: "user",
                    width: {
                        ideal: 640
                    },
                    height: {
                        ideal: 480
                    }
                },

                audio: false

            });


        video.srcObject = cameraStream;

        await video.play();


        status.textContent =
            "Camera ready. Face clearly visible.";

        status.classList.remove("error");

        status.classList.add("success");

        captureBtn.disabled = false;


        console.log("Camera started successfully");


    } catch (error) {

        console.error(
            "Camera Error:",
            error
        );

        status.textContent =
            "Camera permission denied or camera unavailable.";

        status.classList.remove("success");

        status.classList.add("error");

        captureBtn.disabled = true;

        alert(
            "Camera access required.\n\n" +
            "Please allow camera permission in your browser."
        );
    }
}


// ==========================================
// CAPTURE PHOTO
// ==========================================

function capturePhoto() {

    const video = document.getElementById("camera");

    const canvas = document.getElementById("canvas");

    const preview =
        document.getElementById("photoPreview");

    const livePhoto =
        document.getElementById("live_photo");

    const status =
        document.getElementById("cameraStatus");

    const captureBtn =
        document.getElementById("captureBtn");

    const retakeBtn =
        document.getElementById("retakeBtn");


    if (!video || !canvas || !livePhoto) {

        alert(
            "Camera elements not found."
        );

        return;
    }


    if (!cameraStream) {

        alert(
            "Camera is not started. " +
            "Please allow camera permission."
        );

        return;
    }


    // ==========================================
    // CANVAS SIZE
    // ==========================================

    const width = video.videoWidth;
    const height = video.videoHeight;


    if (!width || !height) {

        alert(
            "Camera is not ready yet. " +
            "Please wait for the camera."
        );

        return;
    }


    canvas.width = width;
    canvas.height = height;


    // ==========================================
    // DRAW VIDEO FRAME
    // ==========================================

    const context =
        canvas.getContext("2d");


    // Since video is mirrored using CSS,
    // capture normal image

    context.drawImage(
        video,
        0,
        0,
        width,
        height
    );


    // ==========================================
    // CONVERT TO JPEG
    // ==========================================

    const imageData =
        canvas.toDataURL(
            "image/jpeg",
            0.85
        );


    // ==========================================
    // PUT IMAGE INTO HIDDEN INPUT
    // ==========================================

    livePhoto.value = imageData;


    // ==========================================
    // SHOW PREVIEW
    // ==========================================

    preview.src = imageData;

    preview.style.display = "block";

    video.style.display = "none";


    // ==========================================
    // BUTTONS
    // ==========================================

    captureBtn.style.display = "none";

    retakeBtn.style.display = "inline-block";


    // ==========================================
    // STATUS
    // ==========================================

    status.textContent =
        "✓ Live photo captured successfully.";

    status.classList.remove("error");

    status.classList.add("success");


    photoCaptured = true;


    // ==========================================
    // STOP CAMERA
    // ==========================================

    stopCamera();


    // ==========================================
    // UPDATE SUBMIT BUTTON
    // ==========================================

    updateSubmitButton();


    console.log(
        "Photo captured successfully"
    );
}


// ==========================================
// RETAKE PHOTO
// ==========================================

function retakePhoto() {

    const video =
        document.getElementById("camera");

    const preview =
        document.getElementById("photoPreview");

    const livePhoto =
        document.getElementById("live_photo");

    const captureBtn =
        document.getElementById("captureBtn");

    const retakeBtn =
        document.getElementById("retakeBtn");

    const status =
        document.getElementById("cameraStatus");


    // Clear old photo

    livePhoto.value = "";

    photoCaptured = false;


    // Show camera

    preview.style.display = "none";

    video.style.display = "block";


    // Buttons

    captureBtn.style.display =
        "inline-block";

    retakeBtn.style.display =
        "none";


    status.textContent =
        "Starting camera...";

    status.classList.remove(
        "success",
        "error"
    );


    // Start camera again

    startCamera();


    updateSubmitButton();
}


// ==========================================
// STOP CAMERA
// ==========================================

function stopCamera() {

    if (cameraStream) {

        cameraStream
            .getTracks()
            .forEach(function (track) {

                track.stop();

            });

        cameraStream = null;
    }
}


// ==========================================
// ENABLE / DISABLE SUBMIT
// ==========================================

function updateSubmitButton() {

    const submitBtn =
        document.getElementById("submitVote");

    if (!submitBtn) {
        return;
    }


    const selectedCandidate =
        document.querySelector(
            'input[name="candidate_name"]:checked'
        );


    const livePhoto =
        document.getElementById("live_photo");


    const candidateSelected =
        selectedCandidate !== null;


    const photoReady =
        livePhoto &&
        livePhoto.value !== "";


    // Both required

    if (
        candidateSelected &&
        photoReady
    ) {

        submitBtn.disabled = false;

        submitBtn.textContent =
            "🗳️ Cast Vote Securely";

    } else {

        submitBtn.disabled = true;

        if (!candidateSelected) {

            submitBtn.textContent =
                "Select Candidate First";

        } else if (!photoReady) {

            submitBtn.textContent =
                "Capture Photo First";
        }
    }
}


// ==========================================
// FORM SUBMIT VALIDATION
// ==========================================

document.addEventListener(
    "submit",
    function (event) {

        const form =
            document.getElementById("voteForm");

        if (!form) {
            return;
        }


        const selectedCandidate =
            document.querySelector(
                'input[name="candidate_name"]:checked'
            );


        const livePhoto =
            document.getElementById("live_photo");


        // Candidate check

        if (!selectedCandidate) {

            event.preventDefault();

            alert(
                "Please select a candidate first."
            );

            return;
        }


        // Photo check

        if (
            !livePhoto ||
            !livePhoto.value
        ) {

            event.preventDefault();

            alert(
                "Please capture your live photo first."
            );

            return;
        }


        console.log(
            "Submitting vote:",
            selectedCandidate.value
        );

    }
);


// ==========================================
// PAGE EXIT
// ==========================================

window.addEventListener(
    "beforeunload",
    function () {

        stopCamera();

    }
);
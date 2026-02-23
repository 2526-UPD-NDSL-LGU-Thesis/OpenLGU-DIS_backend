const steps = document.querySelectorAll(".step");
const qrInput = document.getElementById("qrImage");

let userName;
let philsysCardNumber;
let faceData;

qrInput.addEventListener("change", () => {
    const file = qrInput.files[0];
    if (!file) return;

    const reader = new FileReader();

    reader.onloadend = async () => {
        try {
            const base64Image = reader.result;

            const res = await fetch("/api/read/", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ qr_data: base64Image })
            });

            if (!res.ok) {
                throw new Error("QR read failed");
            }

            const data = await res.json();

            // ✅ Fill Step 1 fields
            document.getElementById("PCN").value    = data.pcn;
            document.getElementById("name").value   = data.name;
            document.getElementById("DOB").value    = data.dob;

        } catch (err) {
            console.error("QR processing error:", err);
            alert("Failed to process QR code");
        }
    };

    reader.readAsDataURL(file);
});


function showStep(stepNumber) {
    steps.forEach((step, index) => {
        step.classList.toggle("active", index === stepNumber - 1);
    });
}

document.getElementById("verifyStep1").addEventListener("click", async () => {
    const btn = document.getElementById("verifyStep1");

    const PCN  = document.getElementById("PCN").value;
    const name = document.getElementById("name").value;
    const DOB  = document.getElementById("DOB").value;

    philsysCardNumber = PCN;
    userName = name;

    if (!PCN || !name || !DOB) {
        alert("Please complete all fields");
        return;
    }

    btn.disabled = true;
    const originalText = btn.textContent;
    btn.textContent = "Verifying...";

    try {
        const res = await fetch("/api/verify/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ PCN, name, DOB })
        });

        if (!res.ok) {
            throw new Error("Authentication failed");
        }

        const data = await res.json();

        showStep(2); // ✅ THIS WILL NOW WORK
        
        const img = document.getElementById("facePreview");
        img.src = "data:image/jpg;base64," + data.face;
        img.style.display = "block";

        const cap = document.getElementById("capturePreview");
        cap.src = "data:image/jpg;base64," + data.face;
        cap.style.display = "block";

        faceData = data.face;

    } catch (err) {
        console.error(err);
        alert("Failed to verify PCN.");

        btn.disabled = false;
        btn.textContent = originalText;
    }
});

document.getElementById("confirmFace").disabled = true;

const img = document.getElementById("facePreview");
img.onload = () => {
    document.getElementById("confirmFace").disabled = false;
};

document.getElementById("confirmFace").addEventListener("click", () => {
    showStep(3);
});

document.getElementById("wrongFace").addEventListener("click", () => {
    alert("Please re-upload the QR code or verify your details.");

    showStep(1);

    const btn = document.getElementById("verifyStep1");
    btn.disabled = false;
    btn.textContent = "Verify";
});

document.getElementById("registrationForm").addEventListener("submit", async (e) => {
    e.preventDefault();

    const formData = new FormData(e.target);

    const requestBody = new FormData();
    requestBody.append("pcn", formData.get("PCN"));
    requestBody.append("proof_of_residence", formData.get("proof"));
    requestBody.append("verified", true);

    const response = await fetch("/api/ids/", {
        method: "POST",
        body: requestBody
    });

    const data = await response.json();

    showStep(4);
});

const video = document.getElementById("video");
const canvas = document.getElementById("canvas");
const capturePreview = document.getElementById("capturePreview");

const acceptBtn = document.getElementById("acceptCapture");
const rejectBtn = document.getElementById("rejectCapture");

let stream = null;
let cameraRunning = false;
let capturedImageBlob = null;

// Toggle behavior for accept button
acceptBtn.addEventListener("click", async () => {

    // 🔹 If camera NOT running → start camera
    if (!cameraRunning) {
        try {
            stream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: "user" }
            });

            video.srcObject = stream;
            video.style.display = "block";
            capturePreview.style.display = "none";

            acceptBtn.textContent = "Capture";
            cameraRunning = true;

        } catch (err) {
            alert("Camera access denied or unavailable.");
            console.error(err);
        }
    }

    // 🔹 If camera running → capture photo
    else {
        const context = canvas.getContext("2d");

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        context.drawImage(video, 0, 0);

        canvas.toBlob(blob => {
            capturedImageBlob = blob;
        }, "image/jpeg");

        capturePreview.src = canvas.toDataURL("image/jpeg");
        faceData = capturePreview.src;

        // Stop camera after capture
        stream.getTracks().forEach(track => track.stop());

        video.style.display = "none";
        capturePreview.style.display = "block";

        acceptBtn.textContent = "Start Camera";
        cameraRunning = false;
    }
});

// Reject button → stop camera if running
rejectBtn.addEventListener("click", async () => {
    if (cameraRunning && stream) {
        stream.getTracks().forEach(track => track.stop());
    }

    video.style.display = "none";
    cameraRunning = false;
    acceptBtn.textContent = "Start Camera";
    
    showStep(5);

    try {
        const res = await fetch("/api/digitalid/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ userName, philsysCardNumber, faceData })
        });

        if (!res.ok) {
            throw new Error("Generation failed");
        }

        // Get the image as a blob
        const blob = await res.blob();

        // Convert blob to a URL that <img> can use
        const imageUrl = URL.createObjectURL(blob);

        const img = document.getElementById("idImage");
        img.src = imageUrl;
        img.style.display = "block";

    } catch (err) {
        console.error(err);
        alert("Failed to generate ID.");
    }
});
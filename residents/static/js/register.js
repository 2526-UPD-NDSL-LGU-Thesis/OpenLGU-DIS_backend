const steps = document.querySelectorAll(".step");
const qrInput = document.getElementById("qrImage");

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
        console.log("Verify response:", data);

        showStep(2); // ✅ THIS WILL NOW WORK
        
        const img = document.getElementById("facePreview");
        img.src = "data:image/jpg;base64," + data.face;
        img.style.display = "block";
        console.log(img.src);

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
});

document.getElementById("registrationForm").addEventListener("submit", async (e) => {
    e.preventDefault();

    const formData = new FormData(e.target);

    const response = await fetch("/api/ids/", {
        method: "POST",
        body: formData
    });

    const data = await response.json();

    alert("Registration successful!");
});

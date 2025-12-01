// Document elements
const qrInput       = document.getElementById("qrImage");
const downloadBtn   = document.querySelector('.btn.download');
const generateBtn   = document.querySelector('.btn.generate');


// QR File Event Listener
qrInput.addEventListener("change", () => {
    console.log("Reading QR.")
    const file = qrInput.files[0];
    if (!file) return;

    const reader = new FileReader();

    reader.onloadend = () => {
        const base64Image = reader.result;

        fetch("http://127.0.0.1:8000/api/read/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ qr_data: base64Image })
        })
        .then(res => res.json())
        .then(data => {
            if (data[1] === "PH") {
                console.warn("Wrong QR", e);
            } else {
                try {
                    document.getElementById("student_lab_id").textContent       = data.cs_lab_id;
                    document.getElementById("student_dept_id").textContent      = data.cs_dept_id;
                    document.getElementById("student_lab").textContent          = data.cs_lab;
                    document.getElementById("student_date_issued").textContent  = data.issued_at;

                    // Enable buttons
                    downloadBtn.disabled = false;
                    generateBtn.disabled = false;

                    fetch(`http://localhost:8000/api/ids/${data.cs_lab_id}`, {
                        method: "GET",
                        headers: { "Content-Type": "application/json" },
                    }).then(data => {
                        if (data.verified) {
                            statusElement.classList.remove("not-verified");
                            statusElement.classList.add("verified");
                            statusElement.textContent = "Verified";
                        }
                    })

                } catch (e) {
                    console.warn("Unexpected QR data format", e);
                }
            }
        })
        .catch(err => console.error("Error:", err));
    };

    reader.readAsDataURL(file);
})
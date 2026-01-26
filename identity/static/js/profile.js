// Document elements
const qrInput       = document.getElementById("qrImage");
const downloadBtn   = document.querySelector('.btn.download');
const generateBtn   = document.querySelector('.btn.generate');
const statusElement = document.getElementById("verifiedStatus");


// QR File Event Listener
qrInput.addEventListener("change", () => {
    console.log("Reading QR.");
    const file = qrInput.files[0];
    if (!file) return;

    const reader = new FileReader();

    reader.onloadend = () => {
        const base64Image = reader.result;

        fetch("/api/read/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ qr_data: base64Image })
        })
        .then(res => res.json())
        .then(data => {
            // TODO FIX THIS
            if (data[1] === "PH") {
                console.warn("Wrong QR", e);
            } else {
                console.log(data);
                try {
                    document.getElementById("student_lab_id").textContent       = data.user_id;
                    document.getElementById("student_dept_id").textContent      = " ";
                    document.getElementById("student_lab").textContent          = "Manila"
                    document.getElementById("student_date_issued").textContent  = data.issued_at;

                    fetch(`/api/ids/${data.user_id}`, {
                        method: "GET",
                        headers: { "Content-Type": "application/json" },
                    })
                    .then(res =>  res.json())
                    .then(user_data => {
                        console.log(user_data);
                        if (user_data.verified) {
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
});


downloadBtn.addEventListener("click", () => {
    console.log("Hello");

    const uid = document.getElementById("student_lab_id").textContent;

    window.open(`/api/ids/${uid}/id`);
});


generateBtn.addEventListener("click", () => {
    console.log("Hello");

    const uid = document.getElementById("student_lab_id").textContent;

    window.open(`/api/ids/${uid}/qr`);
});
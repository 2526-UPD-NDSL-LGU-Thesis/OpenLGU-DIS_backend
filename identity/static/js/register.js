const qrInput       = document.getElementById("qrImage");
const labsSelect    = document.getElementById("labs");
const resultBox    = document.getElementById("result");
const registerRes  = document.getElementById("labid");
const registerBtn   = document.getElementById("register");

// QR File Event Listener
qrInput.addEventListener("change", () => {
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
                // Fill in form fields (guard accesses)
                try {
                    document.getElementById("d").value    = data[169]['d'];
                    document.getElementById("i").value    = data[169]['i'];
                    document.getElementById("s").value    = data[169]['sb']['s'];
                    document.getElementById("name").value = 
                        `${data[169]['sb']['fn']} ${data[169]['sb']['mn']} ${data[169]['sb']['ln']}`;
                    document.getElementById("DOB").value  = data[169]['sb']['DOB'];
                    document.getElementById("PCN").value  = data[169]['sb']['PCN'];
                    document.getElementById("POB").value  = data[169]['sb']['POB'];
                } catch (e) {
                    console.warn("Unexpected QR data format", e);
                }
            } else {
                console.warn("Wrong QR", e);
            }
        })
        .catch(err => console.error("Error:", err));
    };

    reader.readAsDataURL(file);
});


// // Add selection for labs
// if (labsSelect) {
//     fetch("/api/labs"
//     ).then(res => res.json()
//     ).then(data => {
//         labsSelect.innerHTML = "";
//         if (Array.isArray(data)) {
//             data.forEach(lab => {
//                 const opt = document.createElement("option");
//                 opt.value = lab.abbr ?? lab.name ?? lab;
//                 opt.textContent = lab.name ?? lab;
//                 labsSelect.appendChild(opt);
//             });
//         }
//     })
//     .catch(err => {
//         console.warn("Failed to load labs:", err);
//         labsSelect.disabled = true;
//     });
// }


// Submit form
registerBtn.addEventListener("click", async (event) => {
    event.preventDefault();

    const regForm = document.getElementById("registrationForm");
    if (!regForm) {
        console.error("registrationForm not found");
        registerBtn.disabled = false;
        registerBtn.textContent = "Register";
        return;
    }

    registerBtn.disabled = true;
    registerBtn.textContent = "Registering...";

    try {
        const regData = new FormData(regForm);
        console.log([...regData.entries()]);

        const csID = new FormData();
        // csID.append("cslab", regData.get("labs"));
        csID.append("pcn", Number(regData.get("PCN")));
        csID.append("file", regData.get("proof"));

        // Check if CSDeptID is already registered:
        const check = await fetch(`/api/ids/${regData.get("PCN")}`)
        
        if (!check.ok) {
            console.log("Panic!");
            return;
        }

        const resp = await fetch("/api/ids/", {
            method: "POST",
            body: csID,
        });

        const body = await resp.json();

        console.log(body);

        if (resp.ok) {
            resultBox.style.backgroundColor = "green";
            resultBox.style.color = "white";
            resultBox.textContent = `Registered successfully (id: ${body.id ?? body.cs_lab_id ?? "created"})`;
            // optionally disable register after success
            registerBtn.disabled = true;

            // show the created id in the labid div
            registerRes.textContent = `Assigned Lab ID: ${body.id ?? body.cs_lab_id ?? "created"}`;

            window.open(`/api/ids/${body.id}/qr`)
        } else {
            resultBox.style.backgroundColor = "red";
            resultBox.style.color = "white";
            resultBox.textContent = body[0].message ?? JSON.stringify(body[0]);
            registerBtn.disabled = false;
        }
    } catch (err) {
        console.error("Registration error:", err);
        resultBox.style.backgroundColor = "red";
        resultBox.style.color = "white";
        resultBox.textContent = "Registration failed.";
        registerBtn.disabled = false;
    } finally {
        registerBtn.textContent = "Register";
    }
});

// export function initRegisterPage() {
//     console.log("Profile page initialized.");

//     const qrInput      = document.getElementById("qrImage");
//     const form         = document.getElementById("sampleForm");
//     const labForm      = document.getElementById("labForm")
//     const verifyButton = document.getElementById("verify");
//     const resultBox    = document.getElementById("result");
//     const labsSelect   = document.getElementById("labs");
//     const registerBtn  = document.getElementById("register");
//     const registerRes  = document.getElementById("labid");

//     if (!qrInput || !form) {
//         console.warn("Scan page elements not found.");
//         return;
//     }

//     // Hide resultBox on load
//     if (resultBox) {
//         resultBox.style.display = "none";
//     }

//     // Populate labs on init
//     if (labsSelect) {
//         fetch("http://LOCALHOST:5000/api/labs", { method: "GET" })
//             .then(res => res.json())
//             .then(data => {
//                 labsSelect.innerHTML = "";
//                 if (Array.isArray(data)) {
//                     data.forEach(lab => {
//                         const opt = document.createElement("option");
//                         opt.value = lab.id ?? lab.name ?? lab;
//                         opt.textContent = lab.name ?? lab;
//                         labsSelect.appendChild(opt);
//                     });
//                 }
//                 // keep select disabled until verification/step-two
//                 // labsSelect.disabled = true;
//             })
//             .catch(err => {
//                 console.warn("Failed to load labs:", err);
//                 labsSelect.disabled = true;
//             });
//     }

//     // -----------------------------------------------
//     // Handle Image Upload
//     // -----------------------------------------------
//     function handleImageUpload(event) {
//         const file = event.target.files[0];
//         if (!file) return;

//         const reader = new FileReader();

//         reader.onloadend = () => {
//             const base64Image = reader.result;

//             fetch("http://LOCALHOST:5000/api/read", {
//                 method: "POST",
//                 headers: { "Content-Type": "application/json" },
//                 body: JSON.stringify({ qr_data: base64Image })
//             })
//             .then(res => res.json())
//             .then(data => {
//                 if (data[1] === "PH") {
//                     // Fill in form fields (guard accesses)
//                     try {
//                         document.getElementById("d").value    = data[169]['d'];
//                         document.getElementById("i").value    = data[169]['i'];
//                         document.getElementById("s").value    = data[169]['sb']['s'];
//                         document.getElementById("name").value = 
//                             `${data[169]['sb']['fn']} ${data[169]['sb']['mn']} ${data[169]['sb']['ln']}`;
//                         document.getElementById("DOB").value  = data[169]['sb']['DOB'];
//                         document.getElementById("PCN").value  = data[169]['sb']['PCN'];
//                         document.getElementById("POB").value  = data[169]['sb']['POB'];
//                     } catch (e) {
//                         console.warn("Unexpected QR data format", e);
//                     }

//                     // show form now that data is available
//                     form.style.display = "block";

//                     // // Immediately submit the form (invokes the submit handler below)
//                     // if (typeof form.requestSubmit === "function") {
//                     //     form.requestSubmit();
//                     // } else {
//                     //     form.dispatchEvent(new Event("submit", { cancelable: true, bubbles: true }));
//                     // }
//                 } else {
//                     console.log(data)
//                     try {
//                         document.getElementById("student_lab_id").value       = data.cs_lab_id;
//                         document.getElementById("student_dept_id").value      = data.cs_dept_id;
//                         document.getElementById("student_lab").value          = data.cs_lab;
//                         document.getElementById("student_date_issued").value  = data.issued_at;

//                     } catch (e) {
//                         console.warn("Unexpected QR data format", e);
//                     }
                    
//                     labForm.style.display = "block";
//                 }
//             })
//             .catch(err => console.error("Error:", err));
//         };

//         reader.readAsDataURL(file);
//     }

//     qrInput.addEventListener("change", handleImageUpload);

//     // -----------------------------------------------
//     // Handle Verification Submission
//     // -----------------------------------------------
//     // form.addEventListener("submit", (event) => {
//     //     event.preventDefault();

//     //     if (verifyButton) {
//     //         verifyButton.disabled = true;
//     //         verifyButton.textContent = "Submitting...";
//     //     }

//     //     const payload = {
//     //         PCN:  document.getElementById("PCN").value,
//     //         name: document.getElementById("name").value,
//     //         DOB:  document.getElementById("DOB").value
//     //     };

//     //     // fetch("http://LOCALHOST:5000/api/verify", {
//     //     fetch("http://LOCALHOST:5000/api/verify", {
//     //         method: "POST",
//     //         headers: { "Content-Type": "application/json" },
//     //         body: JSON.stringify(payload)
//     //     })
//     //     .then(res => res.json())
//     //     .then(data => {
//     //         if (data.status === true) {
//     //             resultBox.style.backgroundColor = "green";
//     //             resultBox.style.color = "white";
//     //             resultBox.textContent = "PCN Verified Successfully!";

//     //             // Show document proof upload step
//     //             document.getElementById("doc-proof-section").style.display = "block";
                
//     //         } else {
//     //             resultBox.style.backgroundColor = "red";
//     //             resultBox.style.color = "white";
//     //             resultBox.textContent = "Invalid Information! Please try again.";
//     //         }

//     //         if (labsSelect) labsSelect.disabled = false;
//     //         if (registerBtn) registerBtn.disabled = false;

//     //         if (verifyButton) {
//     //             verifyButton.disabled = false;
//     //             verifyButton.textContent = "Verify";
//     //         }
//     //     })
//     //     .catch(err => {
//     //         console.error("Error:", err);
//     //         if (verifyButton) {
//     //             verifyButton.disabled = false;
//     //             verifyButton.textContent = "Verify";
//     //         }
//     //     });
//     // });

//     // -----------------------------------------------
//     // Handle Register button: POST to /api/ids
//     // -----------------------------------------------
//     if (registerBtn) {
//         // ensure register button stays disabled until step-two is shown
//         // registerBtn.disabled = true;

//         registerBtn.addEventListener("click", async (e) => {
//             e.preventDefault();

//             const selectedLab = labsSelect ? labsSelect.selectedIndex : -1;
//             const pcn = document.getElementById("PCN").value;

//             const form = document.getElementById("sampleForm")

//             registerBtn.disabled = true;
//             registerBtn.textContent = "Registering...";

//             try {
//                 const formData = new FormData(form);
                
//                 const resp = await fetch("/api/ids", {
//                     method: "POST",
//                     body: formData,
//                 });

//                 const body = await resp.json();   

//                 if (resp.ok) {
//                     resultBox.style.backgroundColor = "green";
//                     resultBox.style.color = "white";
//                     resultBox.textContent = `Registered successfully (id: ${body[0].id ?? body[0].cs_lab_id ?? "created"})`;
//                     // optionally disable register after success
//                     registerBtn.disabled = true;

//                     // show the created id in the labid div
//                     registerRes.textContent = `Assigned Lab ID: ${body[0].id ?? body[0].cs_lab_id ?? "created"}`;
//                 } else {
//                     resultBox.style.backgroundColor = "red";
//                     resultBox.style.color = "white";
//                     resultBox.textContent = body[0].message ?? JSON.stringify(body[0]);
//                     registerBtn.disabled = false;
//                 }
//             } catch (err) {
//                 console.error("Registration error:", err);
//                 resultBox.style.backgroundColor = "red";
//                 resultBox.style.color = "white";
//                 resultBox.textContent = "Registration failed.";
//                 registerBtn.disabled = false;
//             } finally {
//                 registerBtn.textContent = "Register";
//             }
//         });
//     }
// }

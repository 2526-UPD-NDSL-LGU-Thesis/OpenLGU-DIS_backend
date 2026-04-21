let selectedServiceId = null;
let verifiedID = null;
let qrScanner = null;

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookies[i].substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

/* ================= STEP CONTROLLER ================= */

function goToStep(stepId) {
    document.querySelectorAll(".step").forEach(step => {
        step.classList.remove("active");
    });

    document.getElementById(stepId).classList.add("active");
}

/* ================= LOGIN ================= */

document.getElementById("login-btn").addEventListener("click", login);

async function login() {
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    if (!username || !password) {
        alert("Please enter username and password");
        return;
    }

    try {
        const res = await fetch("/api/login/", {
            method: "POST",
            credentials: "include",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken")
            },
            body: JSON.stringify({ username, password })
        });

        const data = await res.json();

        if (!res.ok) {
            alert(data.error || "Login failed");
            return;
        }

        // OPTIONAL: store token if your API returns one
        // localStorage.setItem("token", data.token);

        // Move to next step
        goToStep("step-table");
        console.log("Hello");

    } catch (err) {
        console.error(err);
        alert("Login error");
    }
}

/* ================= LOAD TABLE ================= */
document.getElementById("claims-dropdown").addEventListener("change", loadClaims);

async function loadClaims() {
    const service = document.getElementById("claims-dropdown").value;

    const res = await fetch(`/api/services/${service}/claims/`, {
        method: "GET",
        credentials: "include",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken")
        },
    });

    const data = await res.json();
    const tableBody = document.getElementById('claims-table-body');
    tableBody.innerHTML = '';

    data.forEach(claim => {
        const row = document.createElement('tr');

        row.innerHTML = `
            <td>${claim.transaction_id}</td>
            <td>${claim.user}</td>
            <td>${claim.service}</td>
            <td>${claim.claimed_at}</td>
            <td>Official #${claim.claimed_by}</td>
        `;

        tableBody.appendChild(row);
    });
};

document.getElementById("proceed-to-service-btn").addEventListener("click", () => {
    loadServices();
    goToStep("step-service");
});


/* ================= LOAD SERVICES ON PAGE LOAD ================= */

window.addEventListener("DOMContentLoaded", () => {
    loadServices();
    goToStep("step-login"); // ensure login is first
});

async function loadServices() {
    const res = await fetch("/api/services/active/", {
        credentials: "include",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken")
        },
    });
    const services = await res.json();

    const dropdown = document.getElementById("service-dropdown");
    const dropdown2 = document.getElementById("claims-dropdown");
    dropdown.innerHTML = "";
    dropdown2.innerHTML = "";

    services.forEach(service => {
        const option = document.createElement("option");
        option.value = service.name;
        option.textContent = service.name;
        dropdown.appendChild(option);
    });

    services.forEach(service => {
        const option = document.createElement("option");
        option.value = service.name;
        option.textContent = service.name;
        dropdown2.appendChild(option);
    });
}

/* ================= START SCANNER ================= */

document.getElementById("start-scan-btn").addEventListener("click", () => {
    try {
        selectedServiceId = document.getElementById("service-dropdown").value;

        qrScanner = new Html5Qrcode("qr-reader");

        qrScanner.start(
            { facingMode: "environment" },
            { fps: 10, qrbox: 250 },
            onScanSuccess
        );

        goToStep("step-scan");
    } catch (error) {
        console.error("Error starting scanner:", error);
    }
});

/* ================= QR SUCCESS ================= */

async function onScanSuccess(decodedText) {
    await qrScanner.stop();
    await processQr(decodedText);
}

/* =================== QR UPLOAD ================== */

const uploadQrInput = document.getElementById("upload-qr");

uploadQrInput.addEventListener("change", async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    try {
        const tempScanner = new Html5Qrcode("qr-reader");
        const decodedText = await tempScanner.scanFile(file, true);

        console.log("QR Code detected:", decodedText);
        await processQr(decodedText);

    } catch (err) {
        console.error("QR decode error:", err);
        alert("Failed to decode QR from uploaded image.");
    }
});

/* =================== PHILSYS QR UPLOAD ================== */

const uploadPhilSysQrInput = document.getElementById("upload-philsys-qr");

uploadPhilSysQrInput.addEventListener("change", async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    try {
        const tempScanner = new Html5Qrcode("qr-reader");

        const decodedText = await tempScanner.scanFile(file, {
            experimentalFeatures: {
                useBarCodeDetectorIfSupported: true
            }
        }, true);

        console.log("PhilSys QR Code detected:", decodedText);

        // OPTIONAL: tag or differentiate PhilSys QR if backend expects it
        await processPhilSysQr(decodedText);

    } catch (err) {
        console.error("PhilSys QR decode error:", err);
        alert("Failed to decode PhilSys QR from uploaded image.");
    }
});

/* =================== PROCESS QR ================== */

async function processQr(decodedText) {
    const res = await fetch(`/api/service/${selectedServiceId}/`, {
        method: "POST",
        credentials: "include",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken")
        },
        body: JSON.stringify({ qr: decodedText })
    });

    const data = await res.json();
    console.log(data);

    if (!res.ok) {
        alert(data.error);
        goToStep("step-service");
        return;
    }

    verifiedID = data.id;

    // goToStep("step-verify");
    goToStep("step-result");
}

async function processPhilSysQr(decodedText) {
    const res = await fetch(`/api/service/${selectedServiceId}/pcn/`, {
        method: "POST",
        credentials: "include",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken")
        },
        body: JSON.stringify({ qr: decodedText })
    });

    const data = await res.json();
    console.log(data);

    if (!res.ok) {
        alert("QR verification failed");
        goToStep("step-service");
        return;
    }

    verifiedID = data.id;

    goToStep("step-verify");
}

/* ================= FACE CONFIRM ================= */

document.getElementById("confirm-yes")
    .addEventListener("click", () => submitClaim(true));

document.getElementById("confirm-no")
    .addEventListener("click", () => submitClaim(false));

async function submitClaim(isMatch) {

    if (!isMatch) {
        document.getElementById("result-message").innerText =
            "Face mismatch. Claim cancelled.";
        goToStep("step-result");
        return;
    }

    const res = await fetch("/api/claim/", {
        method: "POST",
        credentials: "include",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken")
        },
        body: JSON.stringify({
            user_id: verifiedID,
            service_id: selectedServiceId
        })
    });

    const data = await res.json();

    if (res.ok) {
        document.getElementById("result-message").innerText =
            `${data.message} | Remaining: ${data.remaining_claims}`;
    } else {
        document.getElementById("result-message").innerText =
            `Claim failed: ${data.error}`;
    }

    goToStep("step-result");
}

/* ================= RESET FLOW ================= */

document.getElementById("new-claim-btn")
    .addEventListener("click", resetFlow);

function resetFlow() {
    verifiedID = null;
    selectedServiceId = null;
    document.getElementById("qr-reader").innerHTML = "";
    goToStep("step-service");
}
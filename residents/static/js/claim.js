let selectedServiceId = null;
let verifiedID = null;
let qrScanner = null;

/* ================= STEP CONTROLLER ================= */

function goToStep(stepId) {
    document.querySelectorAll(".step").forEach(step => {
        step.classList.remove("active");
    });

    document.getElementById(stepId).classList.add("active");
}

/* ================= LOAD SERVICES ON PAGE LOAD ================= */

window.addEventListener("DOMContentLoaded", loadServices);

async function loadServices() {
    const res = await fetch("/api/services/active");
    const services = await res.json();

    const dropdown = document.getElementById("service-dropdown");
    dropdown.innerHTML = "";

    services.forEach(service => {
        const option = document.createElement("option");
        option.value = service.id;
        option.textContent = service.name;
        dropdown.appendChild(option);
    });
}

/* ================= START SCANNER ================= */

document.getElementById("start-scan-btn").addEventListener("click", () => {
    selectedServiceId = document.getElementById("service-dropdown").value;

    qrScanner = new Html5Qrcode("qr-reader");

    qrScanner.start(
        { facingMode: "environment" },
        { fps: 10, qrbox: 250 },
        onScanSuccess
    );

    goToStep("step-scan");
});

/* ================= QR SUCCESS ================= */

async function onScanSuccess(decodedText) {
    await qrScanner.stop();

    const res = await fetch("/api/authenticate/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ qr: decodedText })
    });

    const data = await res.json();

    if (!res.ok) {
        alert("QR verification failed");
        goToStep("step-service");
        return;
    }

    verifiedID = data.id;
    // document.getElementById("user-image").src = data.image_url;

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
        headers: { "Content-Type": "application/json" },
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
    verifiedPCN = null;
    selectedServiceId = null;
    document.getElementById("qr-reader").innerHTML = "";
    goToStep("step-service");
}
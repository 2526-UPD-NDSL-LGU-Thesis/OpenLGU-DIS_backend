
function showScanner(){
    document.getElementById("upload-section").style.display = "none";
    document.getElementById("qr-section").style.display = "block";

    const scanner = new Html5Qrcode("qr-reader");

    scanner.start(
        { facingMode: "environment" },
        { fps: 10, qrbox: 250 },
        qrCodeMessage => {
            scanner.stop();
            processQR(qrCodeMessage);
        }
    );
}

function uploadQR() {

    const fileInput = document.getElementById("qrFile");

    if (!fileInput.files.length) {
        alert("Please upload a QR image");
        return;
    }

    const file = fileInput.files[0];

    const formData = new FormData();
    formData.append("qr_image", file);

    fetch("/api/upload-qr/", {
        method: "POST",
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        processQR(data); // assuming backend returns decoded text
    })
    .catch(error => {
        console.error(error);
        alert("Upload failed");
    });
}

function processQR(data){

    console.log(data);

    if (data.error) {
        console.error("QR decoding failed:", data.error);
        alert(`Error: ${data.error}`);
    }

    document.getElementById("result-section").style.display = "flex";

    document.getElementById("user_image").src = "data:image/jpg;base64," + data.face_data;
    document.getElementById("id").innerText = data.id;
    document.getElementById("pcn").innerText = data.pcn;
    document.getElementById("issued_at").innerText = data.issued_at;
    document.getElementById("email").innerText = data.email;
    document.getElementById("phone_number").innerText = data.phone_number;

    const verified = document.getElementById("verified_status");

    if(data.verified){
        verified.innerText = "Verified";
        verified.classList.remove("not-verified");
        verified.classList.add("verified");
    }else{
        verified.innerText = "Not Verified";
    }

}

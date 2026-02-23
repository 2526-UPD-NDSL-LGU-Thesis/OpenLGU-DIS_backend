const statusElement = document.getElementById("verifiedStatus");

function searchProfile() {
    const id = document.getElementById("searchID").value;

    if (!id) {
        alert("Please enter an LGU ID.");
        return;
    }

    console.log("Searching for:", id);

    fetch(`/api/ids/${id}`, {
        method: "GET",
        headers: { "Content-Type": "application/json" },
    })
    .then(res =>  res.json())
    .then(user_data => {
        document.getElementById("lgu_id").textContent    = user_data.id;
        document.getElementById("pcn").textContent       = user_data.pcn;
        document.getElementById("issued_at").textContent = user_data.issued_at
        if (user_data.verified) {
            statusElement.classList.remove("not-verified");
            statusElement.classList.add("verified");
            statusElement.textContent = "Verified";
        }
    })
}

let txn;

async function openOTPModal() {
    const pcn = document.getElementById("pcn").textContent;

    const res = await fetch("/api/startotp/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pcn })
    });

    if (!res.ok) {
        throw new Error("OTP Authentication failed!");
    }

    const data = await res.json();

    txn = data.txn;

    document.getElementById("otpModal").style.display = "flex";
}

function closeOTPModal() {
    document.getElementById("otpModal").style.display = "none";
}

async function verifyOTP() {
    const pcn = document.getElementById("pcn").textContent;
    const otp = document.getElementById("otpInput").value;

    if (!otp) {
        alert("Please enter OTP.");
        return;
    }

    console.log("Verifying OTP:", otp);

    await fetch("/api/otp/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pcn, txn, otp })
    })
    .then(res => res.json())
    .then(data => {
        closeOTPModal();

        console.log(data);
        addInfoItem("Name:", data.name.eng, "name");
        addInfoItem("Gender:", data.gender.eng, "gender");
        addInfoItem("Date of Birth:", data.dob, "dob");
        addInfoItem("Email:", data.email, "email");
        addInfoItem("Address:", data.location1.eng, "loc1");
        addInfoItem("Phone:", data.phone, "phone");

        // const img = document.getElementById("")
    });
}

// Auto-fill search input from URL like /profile/1
document.addEventListener("DOMContentLoaded", () => {
    const idInput = document.getElementById("searchID");
    if (idInput.value) {
        searchProfile();
    }
});
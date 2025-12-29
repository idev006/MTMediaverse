// ฟังก์ชันแปลง Base64 เป็น Blob (หัวใจสำคัญของการ Reverse Engineering)
function base64ToBlob(base64, mimeType) {
    const byteCharacters = atob(base64);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    return new Blob([byteArray], { type: mimeType });
}

async function fetchAndUploadLab() {
    const API_URL = "http://127.0.0.1:8000/api/get-video";

    // 1. สร้าง Request Envelope
    const requestPayload = {
        type: "file_request",
        fileId: "my_test_video_01"
    };

    try {
        console.log("📨 ส่ง Request ไป Localhost...");
        const response = await fetch(API_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(requestPayload)
        });

        const envelope = await response.json();

        // 2. แกะซอง (Unwrap Envelope)
        const message = envelope.messages[0]; // สมมุติว่าเอา message แรก

        if (message.type === "video" && message.contentProvider.encoding === "base64") {
            console.log("📦 ได้รับ Video Package ID:", message.packageId);

            // 3. แปลง Payload (Base64) -> Blob
            const videoBlob = base64ToBlob(message.payload, "video/mp4");
            console.log("🔹 แปลงเป็น Blob สำเร็จ! ขนาด:", videoBlob.size, "bytes");

            // 4. สร้าง File Object
            const file = new File([videoBlob], "lab_video.mp4", { type: "video/mp4" });

            // 5. Inject เข้า Shopee (โค้ดเดิม)
            const inputElement = document.querySelector("input.eds-react-upload__input[type='file']");
            if (inputElement) {
                const dataTransfer = new DataTransfer();
                dataTransfer.items.add(file);
                inputElement.files = dataTransfer.files;
                inputElement.dispatchEvent(new Event('change', { bubbles: true }));
                console.log("✅ ยัดไฟล์เข้า Input สำเร็จ!");
            } else {
                console.error("❌ ไม่เจอ Input Element (ต้องรันในหน้า Shopee Upload)");
            }

        }

    } catch (error) {
        console.error("💥 Error:", error);
    }
}

// วิธีเรียกใช้: พิมพ์คำสั่งนี้ใน Console ของ Browser
// fetchAndUploadLab();
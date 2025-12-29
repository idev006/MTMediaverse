// Content Script - ทำงานบนหน้า Shopee Creator Center

// ฟังก์ชันแปลง Base64 เป็น Blob
function base64ToBlob(base64, mimeType) {
    const byteCharacters = atob(base64);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    return new Blob([byteArray], { type: mimeType });
}

// ฟังก์ชัน inject file เข้า input
function injectFileToInput(file) {
    const inputElement = document.querySelector("input.eds-react-upload__input[type='file']");
    if (inputElement) {
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);
        inputElement.files = dataTransfer.files;
        inputElement.dispatchEvent(new Event('change', { bubbles: true }));
        console.log("✅ [Content Script] ยัดไฟล์เข้า Input สำเร็จ!");
        return true;
    } else {
        console.error("❌ [Content Script] ไม่เจอ Input Element");
        return false;
    }
}

// รับ message จาก popup หรือ background
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    console.log("📩 [Content Script] ได้รับ message:", request);

    if (request.action === "uploadVideo") {
        const { base64Data, fileName } = request;

        try {
            // แปลง Base64 เป็น File
            const videoBlob = base64ToBlob(base64Data, "video/mp4");
            const file = new File([videoBlob], fileName || "video.mp4", { type: "video/mp4" });

            // Inject เข้า input
            const success = injectFileToInput(file);
            sendResponse({ success, message: success ? "Upload started" : "Input not found" });
        } catch (error) {
            console.error("💥 [Content Script] Error:", error);
            sendResponse({ success: false, message: error.message });
        }
    }

    return true; // Keep message channel open for async response
});

console.log("🔌 [Shopee Video Uploader] Content Script loaded!");

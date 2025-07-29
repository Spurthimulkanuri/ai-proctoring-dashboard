// 📁 static/js/proctor.js

let warningCount = 0;
let phoneDetectedCount = 0;
let voiceViolationCount = 0;
let previousMouthOpen = false;
let mouthViolationCount = 0;

function captureViolation(type) {
  const video = document.getElementById('video');
  const canvas = document.createElement('canvas');
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  canvas.getContext('2d').drawImage(video, 0, 0);
  const dataURL = canvas.toDataURL('image/jpeg');

  fetch('/upload_snapshot', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      image: dataURL,
      student_id: CURRENT_USER,
      violation_type: type
    })
  });
}

async function startFaceDetection(video) {
  await faceapi.nets.tinyFaceDetector.loadFromUri('/static/models');
  console.log("✅ Face API loaded.");

  while (true) {
    const detections = await faceapi.detectAllFaces(video, new faceapi.TinyFaceDetectorOptions());
    console.log(`👁️ Faces detected: ${detections.length}`);

    if (detections.length !== 1) {
      warningCount++;
      document.getElementById("violations").value = warningCount;
      captureViolation("noface");
      alert(`⚠️ Face count = ${detections.length}. Warning #${warningCount}`);
    }

    if (warningCount >= 3) {
      alert("🚫 Too many face violations. Submitting exam...");
      document.getElementById("examForm").submit();
      break;
    }

    await new Promise(resolve => setTimeout(resolve, 3000));
  }
}

async function checkMouthMovement() {
  const video = document.getElementById('video');
  const detections = await faceapi.detectSingleFace(video, new faceapi.TinyFaceDetectorOptions()).withFaceLandmarks();

  if (detections) {
    const mouth = detections.landmarks.getMouth();
    const [topLip, bottomLip] = [mouth[14], mouth[18]];
    const dist = Math.abs(topLip.y - bottomLip.y);

    let isMouthOpen = dist > 10;
    if (previousMouthOpen && isMouthOpen) {
      mouthViolationCount++;
      if (mouthViolationCount > 5) {
        captureViolation("talking");
        mouthViolationCount = 0;
      }
    } else {
      mouthViolationCount = 0;
    }
    previousMouthOpen = isMouthOpen;
  }
}

async function startPhoneDetection(video) {
  const model = await cocoSsd.load();
  console.log("✅ coco-ssd Model loaded.");

  while (true) {
    const predictions = await model.detect(video);
    const phoneFound = predictions.some(p => p.class === "cell phone" && p.score > 0.5);

    if (phoneFound) {
      phoneDetectedCount++;
      document.getElementById("violations").value = phoneDetectedCount;
      captureViolation("phone");
      alert(`📱 Phone Detected! Warning #${phoneDetectedCount}`);
    }

    if (phoneDetectedCount >= 2) {
      alert("🚨 Phone cheating detected. Submitting exam...");
      document.getElementById("examForm").submit();
      break;
    }

    await new Promise(resolve => setTimeout(resolve, 4000));
  }
}

async function startVoiceDetection() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const mic = audioContext.createMediaStreamSource(stream);
    const analyser = audioContext.createAnalyser();

    mic.connect(analyser);
    const data = new Uint8Array(analyser.fftSize);

    setInterval(() => {
      analyser.getByteFrequencyData(data);
      const volume = data.reduce((sum, val) => sum + val, 0) / data.length;

      console.log("🎙️ Volume:", volume);

      if (volume > 4) {
        voiceViolationCount++;
        document.getElementById("violations").value = voiceViolationCount;
        if (voiceViolationCount === 1) {
          captureViolation("voice");
        }
        alert(`🔊 Suspicious Sound Detected! Warning #${voiceViolationCount}`);
      }

      if (voiceViolationCount >= 2) {
        alert("🚨 Voice cheating detected. Submitting exam...");
        document.getElementById("examForm").submit();
      }
    }, 4000);

  } catch (err) {
    console.error("❌ Mic access error:", err);
    alert("❌ Unable to access microphone.");
  }
}

async function startFaceAndPhoneDetection() {
  const video = document.getElementById("video");

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true });
    video.srcObject = stream;
    console.log("🎥 Webcam started.");

    startFaceDetection(video);
    startPhoneDetection(video);
    startVoiceDetection();

  } catch (err) {
    alert("❌ Unable to access webcam or mic.");
    console.error(err);
  }
}

// 💬 Auto mouth movement detection every 2s
setInterval(checkMouthMovement, 2000);


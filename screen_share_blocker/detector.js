setInterval(() => {
  navigator.mediaDevices.enumerateDevices().then(devices => {
    const displayDevices = devices.filter(d => d.kind === 'videoinput' && d.label.toLowerCase().includes('screen'));
    if (displayDevices.length > 0) {
      alert("⚠️ Screen recording or screen share detected! Exam may be auto-submitted.");
      // Optionally call: document.getElementById("examForm").submit();
    }
  });
}, 5000);


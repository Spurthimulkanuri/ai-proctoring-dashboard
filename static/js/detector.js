(function() {
  const originalGetDisplayMedia = navigator.mediaDevices.getDisplayMedia;

  navigator.mediaDevices.getDisplayMedia = async function(...args) {
    alert("⚠️ Screen sharing detected! This is not allowed during exams.");
    // 🚨 Auto-submit if needed:
    const form = document.getElementById("examForm");
    if (form) form.submit();
    return originalGetDisplayMedia.apply(this, args);
  };
})();


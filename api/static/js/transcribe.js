(function ($) {
  "use strict";

  let passwordValidated = false;
  let selectedFile = null;
  let currentJobId = null;
  let audioDuration = 0;
  let eventSource = null;
  let streamFinished = false;
  let retryCount = 0;
  let retryTimeout = null;

  const MAX_SSE_RETRIES = 5;
  const SSE_INITIAL_RETRY_DELAY_MS = 2000;

  $(document).ready(function () {
    initEventHandlers();
  });

  function initEventHandlers() {
    // Password validation
    $("#ast-validate-btn").on("click", validatePassword);
    $("#ast-password").on("keypress", function (e) {
      if (e.which === 13) {
        validatePassword();
      }
    });

    // File selection
    $("#ast-select-file-btn").on("click", function () {
      $("#ast-file-input").click();
    });

    $("#ast-file-input").on("change", handleFileSelect);

    // Drag and drop
    const uploadArea = $("#ast-upload-area");
    uploadArea.on("dragover", function (e) {
      e.preventDefault();
      $(this).addClass("ast-drag-over");
    });

    uploadArea.on("dragleave", function (e) {
      e.preventDefault();
      $(this).removeClass("ast-drag-over");
    });

    uploadArea.on("drop", function (e) {
      e.preventDefault();
      $(this).removeClass("ast-drag-over");
      const files = e.originalEvent.dataTransfer.files;
      if (files.length > 0) {
        selectedFile = files[0];
        displaySelectedFile(selectedFile);
      }
    });

    // Upload button (step 1: upload file)
    $("#ast-upload-btn").on("click", uploadFile);

    // Time range inputs — format on blur
    $("#ast-start-time, #ast-end-time").on("blur", function () {
      const secs = parseMMSS($(this).val());
      if (secs !== null) {
        $(this).val(formatTime(secs)).removeClass("ast-input-error");
      } else {
        $(this).addClass("ast-input-error");
      }
      hideError("#ast-range-error");
    });

    // Start transcription button (step 2: confirm range and begin)
    $("#ast-start-btn").on("click", beginTranscription);

    // Copy button
    $("#ast-copy-btn").on("click", copyToClipboard);

    // Download button
    $("#ast-download-btn").on("click", downloadTranscript);

    // Stop button
    $("#ast-stop-btn").on("click", stopTranscription);
  }

  function validatePassword() {
    const password = $("#ast-password").val();

    if (!password) {
      showError("#ast-password-error", astData.strings.passwordRequired);
      return;
    }

    $.ajax({
      url: astData.ajaxUrl,
      method: "POST",
      data: {
        action: "ast_validate_password",
        nonce: astData.nonce,
        password: password,
      },
      success: function (response) {
        if (response.success) {
          passwordValidated = true;
          $("#ast-password-section").slideUp();
          $("#ast-upload-section").slideDown();
        } else {
          showError("#ast-password-error", response.data.message);
        }
      },
      error: function () {
        showError("#ast-password-error", astData.strings.uploadError);
      },
    });
  }

  function handleFileSelect(e) {
    const files = e.target.files;
    if (files.length > 0) {
      selectedFile = files[0];
      displaySelectedFile(selectedFile);
    }
  }

  function displaySelectedFile(file) {
    // Validate file type
    const validTypes = ["audio/wav", "audio/x-wav", "audio/m4a", "audio/x-m4a"];
    const fileExt = file.name.split(".").pop().toLowerCase();

    if (!validTypes.includes(file.type) && fileExt !== "wav" && fileExt !== "m4a") {
      showError("#ast-error-section", astData.strings.invalidFileType);
      return;
    }

    // Validate file size
    if (file.size > astData.maxFileSize) {
      showError("#ast-error-section", astData.strings.fileTooLarge);
      return;
    }

    $("#ast-selected-file")
      .html("<strong>" + file.name + "</strong> (" + formatFileSize(file.size) + ")")
      .show();
    $("#ast-upload-btn").show();
    $("#ast-range-section").hide();
    hideError("#ast-error-section");
  }

  // Step 1: Upload the file, get duration, show range picker
  function uploadFile() {
    if (!selectedFile) {
      showError("#ast-error-section", astData.strings.fileRequired);
      return;
    }

    const formData = new FormData();
    formData.append("file", selectedFile);

    $("#ast-upload-btn").prop("disabled", true).text("Uploading\u2026");
    hideError("#ast-error-section");

    $.ajax({
      url: astData.apiUrl + "/api/upload",
      method: "POST",
      data: formData,
      processData: false,
      contentType: false,
      success: function (response) {
        currentJobId = response.job_id;
        audioDuration = response.duration || 0;
        $("#ast-upload-btn").prop("disabled", false).text("Upload File");
        showRangeSection(audioDuration);
      },
      error: function () {
        $("#ast-upload-btn").prop("disabled", false).text("Upload File");
        showError("#ast-error-section", astData.strings.uploadError);
      },
    });
  }

  function showRangeSection(duration) {
    var maxLabel = duration > 0 ? formatTime(duration) : "unknown";
    $("#ast-max-duration-text").text("Max duration: " + maxLabel);
    $("#ast-start-time").val("00:00:00").removeClass("ast-input-error");
    $("#ast-end-time").val(duration > 0 ? formatTime(duration) : "00:00:00").removeClass("ast-input-error");
    hideError("#ast-range-error");
    $("#ast-range-section").slideDown();
  }

  // Step 2: Validate range, POST /api/start, then stream
  function beginTranscription() {
    if (!currentJobId) return;

    const startSecs = parseMMSS($("#ast-start-time").val());
    const endSecs   = parseMMSS($("#ast-end-time").val());

    if (startSecs === null) {
      $("#ast-start-time").addClass("ast-input-error");
      showError("#ast-range-error", "Invalid start time. Use HH:MM:SS format.");
      return;
    }
    if (endSecs === null) {
      $("#ast-end-time").addClass("ast-input-error");
      showError("#ast-range-error", "Invalid end time. Use HH:MM:SS format.");
      return;
    }
    if (startSecs >= endSecs) {
      showError("#ast-range-error", "Start time must be before end time.");
      return;
    }
    if (audioDuration > 0 && endSecs > audioDuration) {
      $("#ast-end-time").addClass("ast-input-error");
      showError("#ast-range-error", "End time exceeds audio duration (" + formatTime(audioDuration) + ").");
      return;
    }

    hideError("#ast-range-error");
    $("#ast-start-btn").prop("disabled", true).text("Starting\u2026");
    $("#ast-upload-btn").prop("disabled", true);

    $.ajax({
      url: astData.apiUrl + "/api/start/" + currentJobId,
      method: "POST",
      contentType: "application/json",
      data: JSON.stringify({ start_seconds: startSecs, end_seconds: endSecs }),
      success: function () {
        $("#ast-start-btn").prop("disabled", false).text("Start Transcription");
        $("#ast-range-section").slideUp();
        $("#ast-progress-section").show();
        updateStatus("Processing\u2026", 20);
        startStreaming(currentJobId);
      },
      error: function (xhr) {
        $("#ast-start-btn").prop("disabled", false).text("Start Transcription");
        $("#ast-upload-btn").prop("disabled", false);
        var msg = (xhr.responseJSON && xhr.responseJSON.error) ? xhr.responseJSON.error : astData.strings.uploadError;
        showError("#ast-range-error", msg);
      },
    });
  }

  function stopTranscription() {
    if (!currentJobId) return;
    // Cancel any pending retry
    if (retryTimeout) {
      clearTimeout(retryTimeout);
      retryTimeout = null;
    }
    const btn = $("#ast-stop-btn");
    btn.prop("disabled", true).text("Stopping...");
    $.ajax({
      url: astData.apiUrl + "/api/stop/" + currentJobId,
      method: "POST",
      error: function () {
        btn.prop("disabled", false).text("Stop Transcription");
      },
    });
  }

  function startStreaming(jobId) {
    streamFinished = false;
    retryCount = 0;
    updateStatus("Streaming transcription...", 25);
    $("#ast-transcription-section").show();
    $("#ast-transcription-text").val("");
    $("#ast-stop-btn").prop("disabled", false).text("Stop Transcription").show();
    connectStream(jobId);
  }

  function connectStream(jobId) {
    if (eventSource) {
      eventSource.close();
      eventSource = null;
    }

    const streamUrl = astData.apiUrl + "/api/stream/" + jobId;
    eventSource = new EventSource(streamUrl);

    eventSource.onmessage = function (event) {
      const data = JSON.parse(event.data);
      handleStreamEvent(data);
    };

    eventSource.onerror = function () {
      // If a terminal event was already handled, the EventSource was closed
      // deliberately — this error callback is a spurious after-close fire.
      if (streamFinished) return;

      eventSource.close();
      eventSource = null;

      if (retryCount < MAX_SSE_RETRIES) {
        const delay = Math.min(SSE_INITIAL_RETRY_DELAY_MS * Math.pow(2, retryCount), 15000);
        retryCount++;
        updateStatus(
          "Connection lost. Reconnecting in " + Math.round(delay / 1000) + "s\u2026 (" + retryCount + "/" + MAX_SSE_RETRIES + ")"
        );
        hideError("#ast-error-section");
        retryTimeout = setTimeout(function () {
          retryTimeout = null;
          connectStream(jobId);
        }, delay);
      } else {
        showError("#ast-error-section", astData.strings.connectionError);
        $("#ast-stop-btn").hide();
        resetUpload();
      }
    };
  }

  function handleStreamEvent(event) {
    switch (event.type) {
      case "connected":
        console.log("Connected to stream");
        break;

      case "started":
        updateStatus("Transcription started...", 30);
        break;

      case "progress": {
        const pct = event.total > 0 ? 30 + (event.processed / event.total) * 65 : 30;
        updateStatus("Processing... " + formatTime(event.processed) + " / " + formatTime(event.total), pct);
        break;
      }

      case "segment":
        appendTranscription(event.timestamp, event.text);
        break;

      case "completed":
        updateStatus("Completed!", 100);
        streamFinished = true;
        retryCount = 0;
        $("#ast-stop-btn").hide();
        $("#ast-download-btn").show();
        $("#ast-upload-btn").prop("disabled", false);
        if (eventSource) {
          eventSource.close();
        }
        break;

      case "stopped":
        updateStatus("Stopped.", 100);
        streamFinished = true;
        retryCount = 0;
        $("#ast-stop-btn").hide();
        if (event.has_content) {
          $("#ast-download-btn").show();
        }
        $("#ast-upload-btn").prop("disabled", false);
        if (eventSource) {
          eventSource.close();
        }
        break;

      case "error":
        showError("#ast-error-section", event.message || "Transcription error");
        streamFinished = true;
        $("#ast-stop-btn").hide();
        resetUpload();
        if (eventSource) {
          eventSource.close();
        }
        break;
    }
  }

  function appendTranscription(timestamp, text) {
    const currentText = $("#ast-transcription-text").val();
    const newText = currentText + timestamp + "\n" + text + "\n\n";
    $("#ast-transcription-text").val(newText);

    // Auto-scroll to bottom
    const textarea = document.getElementById("ast-transcription-text");
    textarea.scrollTop = textarea.scrollHeight;
  }

  function copyToClipboard() {
    const text = $("#ast-transcription-text").val();
    navigator.clipboard.writeText(text).then(function () {
      const btn = $("#ast-copy-btn");
      const originalText = btn.text();
      btn.text(astData.strings.copiedToClipboard);
      setTimeout(function () {
        btn.text(originalText);
      }, 2000);
    });
  }

  function downloadTranscript() {
    if (currentJobId) {
      window.location.href = astData.apiUrl + "/api/download/" + currentJobId;
    }
  }

  function updateStatus(message, progress) {
    $("#ast-status-text").text(message);
    if (progress !== undefined) {
      updateProgress(progress);
    }
  }

  function updateProgress(percent) {
    $("#ast-progress-fill").css("width", percent + "%");
  }

  function resetUpload() {
    $("#ast-upload-btn").prop("disabled", false);
    $("#ast-progress-section").hide();
    updateProgress(0);
  }

  function showError(selector, message) {
    $(selector).text(message).show();
  }

  function hideError(selector) {
    $(selector).hide();
  }

  function formatTime(seconds) {
    const s = Math.floor(seconds);
    const h = Math.floor(s / 3600);
    const m = Math.floor((s % 3600) / 60);
    const rem = s % 60;
    return String(h).padStart(2, "0") + ":" + String(m).padStart(2, "0") + ":" + String(rem).padStart(2, "0");
  }

  /**
   * Parse a "MM:SS" or "H:MM:SS" string into total seconds.
   * Returns null if the format is invalid.
   */
  function parseMMSS(str) {
    if (!str) return null;
    str = str.trim();
    const parts = str.split(":");
    if (parts.length === 2) {
      const m = parseInt(parts[0], 10);
      const s = parseInt(parts[1], 10);
      if (isNaN(m) || isNaN(s) || s < 0 || s > 59 || m < 0) return null;
      return m * 60 + s;
    }
    if (parts.length === 3) {
      const h = parseInt(parts[0], 10);
      const m = parseInt(parts[1], 10);
      const s = parseInt(parts[2], 10);
      if (isNaN(h) || isNaN(m) || isNaN(s) || s < 0 || s > 59 || m < 0 || m > 59 || h < 0) return null;
      return h * 3600 + m * 60 + s;
    }
    return null;
  }

  function formatFileSize(bytes) {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + " " + sizes[i];
  }
})(jQuery);

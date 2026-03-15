(function ($) {
  "use strict";

  let passwordValidated = false;
  let selectedFile = null;
  let currentJobId = null;
  let eventSource = null;

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

    // Upload button
    $("#ast-upload-btn").on("click", startTranscription);

    // Copy button
    $("#ast-copy-btn").on("click", copyToClipboard);

    // Download button
    $("#ast-download-btn").on("click", downloadTranscript);
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
    hideError("#ast-error-section");
  }

  function startTranscription() {
    if (!selectedFile) {
      showError("#ast-error-section", astData.strings.fileRequired);
      return;
    }

    const formData = new FormData();
    formData.append("file", selectedFile);

    // Show progress
    $("#ast-upload-btn").prop("disabled", true);
    $("#ast-progress-section").show();
    updateStatus("Uploading...", 10);

    // Upload file
    $.ajax({
      url: astData.apiUrl + "/api/upload",
      method: "POST",
      data: formData,
      processData: false,
      contentType: false,
      xhr: function () {
        const xhr = new window.XMLHttpRequest();
        xhr.upload.addEventListener(
          "progress",
          function (e) {
            if (e.lengthComputable) {
              const percentComplete = (e.loaded / e.total) * 100;
              updateProgress(percentComplete * 0.2); // Upload is 20% of total
            }
          },
          false,
        );
        return xhr;
      },
      success: function (response) {
        currentJobId = response.job_id;
        updateStatus("Processing...", 20);
        startStreaming(currentJobId);
      },
      error: function () {
        showError("#ast-error-section", astData.strings.uploadError);
        resetUpload();
      },
    });
  }

  function startStreaming(jobId) {
    updateStatus("Streaming transcription...", 25);
    $("#ast-transcription-section").show();
    $("#ast-transcription-text").val("");

    const streamUrl = astData.apiUrl + "/api/stream/" + jobId;
    eventSource = new EventSource(streamUrl);

    eventSource.onmessage = function (event) {
      const data = JSON.parse(event.data);
      handleStreamEvent(data);
    };

    eventSource.onerror = function () {
      if (eventSource.readyState === EventSource.CLOSED) {
        console.log("Stream closed");
      } else {
        showError("#ast-error-section", astData.strings.connectionError);
      }
      eventSource.close();
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

      case "segment":
        appendTranscription(event.timestamp, event.text);
        updateProgress(50); // Segments coming in
        break;

      case "completed":
        updateStatus("Completed!", 100);
        $("#ast-download-btn").show();
        $("#ast-upload-btn").prop("disabled", false);
        if (eventSource) {
          eventSource.close();
        }
        break;

      case "error":
        showError("#ast-error-section", event.message || "Transcription error");
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

  function formatFileSize(bytes) {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + " " + sizes[i];
  }
})(jQuery);

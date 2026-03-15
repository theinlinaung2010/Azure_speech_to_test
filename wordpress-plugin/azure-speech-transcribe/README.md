# Azure Speech Transcribe WordPress Plugin

Password-protected audio transcription plugin with real-time streaming display using Azure Speech-to-Text API.

## Features

- Password-protected access
- Drag-and-drop file upload
- Real-time transcription streaming
- Support for WAV and M4A formats
- Auto-scrolling transcript display
- Copy to clipboard functionality
- Download completed transcripts
- Rate limiting (5 attempts per 5 minutes)
- Responsive design

## Installation

1. Upload the `azure-speech-transcribe` folder to `/wp-content/plugins/`
2. Activate the plugin through the 'Plugins' menu in WordPress
3. Go to Settings > Azure Speech Transcribe to configure

## Configuration

### Plugin Settings

Navigate to **Settings > Azure Speech Transcribe**:

- **Access Password**: Password users must enter to access the transcription form
- **Flask API URL**: URL of your Flask API server (e.g., http://localhost:5000)
- **Max File Size**: Maximum allowed file size in megabytes

### Flask API Setup

The plugin requires a running Flask API server. See the `api` directory for setup instructions.

## Usage

1. Add the shortcode to any page or post:

```
[azure_transcribe]
```

2. Users will see a password-protected form
3. After validation, they can upload audio files
4. Transcription will stream in real-time to the textarea
5. Once complete, users can copy or download the transcript

## Shortcode

```
[azure_transcribe]
```

No attributes required.

## Security Features

- Password validation via AJAX
- WordPress nonce verification
- File type validation (WAV, M4A only)
- File size limits
- Rate limiting on password attempts (5 per 5 minutes)
- Sanitized filenames
- CORS support configured in Flask API

## Customization

### Styling

Edit `/assets/css/transcribe.css` to customize the appearance.

### JavaScript

Edit `/assets/js/transcribe.js` to modify behavior.

### Template

Edit `/templates/transcribe-form.php` to change the HTML structure.

## Requirements

- WordPress 5.0+
- PHP 7.4+
- Running Flask API server
- jQuery (included with WordPress)

## Troubleshooting

### "Connection error" message

- Verify Flask API is running
- Check API URL in plugin settings
- Ensure CORS is properly configured

### "Invalid password" not working

- Check password in Settings > Azure Speech Transcribe
- Clear browser cache
- Check PHP error logs

### Upload fails

- Verify file size is within limits
- Check file format (WAV or M4A only)
- Ensure Flask API is accessible

## Development

### File Structure

```
azure-speech-transcribe/
├── azure-speech-transcribe.php    # Main plugin file
├── includes/
│   ├── class-admin-settings.php   # Admin settings page
│   ├── class-shortcode.php        # Shortcode handler
│   └── class-ajax-handler.php     # AJAX handlers
├── assets/
│   ├── css/
│   │   └── transcribe.css         # Styles
│   └── js/
│       └── transcribe.js          # JavaScript
└── templates/
    └── transcribe-form.php        # Form template
```

## Changelog

### Version 1.0.0

- Initial release
- Password protection
- Real-time streaming transcription
- File upload with drag-and-drop
- Copy and download functionality

## License

GPL v2 or later

## Support

For issues or questions, please contact the plugin author.

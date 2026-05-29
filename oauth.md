# Getting OAuth Client ID Credentials

[English](oauth.md) | [日本語](oauth-ja.md)

1. Create a Google Cloud project
   - Open Google Cloud Console
   - Open the project selector
     - Click "New Project"
     - Enter any name (example: google-forms-cli)

2. Enable the Google Forms API and Google Drive API
   - Go to APIs & Services > Library
   - Enable Google Forms API and Google Drive API

3. Configure the OAuth consent screen
   - Go to APIs & Services > OAuth consent screen
   - Open Branding > Get started
   - Example values:
     - App name: Form Sync Toolkit
     - User support email: your Gmail address
     - Audience: External
     - Contact information: your Gmail address

4. Add test users
   - Go to APIs & Services > OAuth consent screen
   - Open Branding > Audience
   - Open Test users > Add users
   - Add your Gmail address

5. Create an OAuth Client ID
   - Go to APIs & Services > Credentials
   - Open Create credentials > OAuth Client ID
   - Example values:
     - Application type: Desktop app
     - Name: Form Sync Toolkit
   - Download and save the JSON file
   - On the first authenticated CLI run, enter that file path when prompted. The toolkit copies it to `~/.config/form-sync-toolkit/credentials.json` with mode `600`.

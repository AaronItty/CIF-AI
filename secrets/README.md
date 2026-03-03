# Secrets Directory

This directory holds sensitive credential files that must **never** be committed to Git.

## Gmail API Setup

1. Go to [Google Cloud Console → APIs & Services → Credentials](https://console.cloud.google.com/apis/credentials)
2. Create an **OAuth 2.0 Client ID** (Desktop application type)
3. Download the JSON and save it here as `credentials.json`
4. On first startup the email service will open a browser for one-time OAuth consent
5. After login, `token.json` is saved here automatically — subsequent startups are fully silent

## Files

| File              | Source                | Gitignored? |
|-------------------|-----------------------|-------------|
| `credentials.json` | Google Cloud Console  | ✅ Yes       |
| `token.json`       | Auto-generated        | ✅ Yes       |
| `.gitkeep`         | Keeps dir in Git      | No          |
| `README.md`        | This file             | No          |

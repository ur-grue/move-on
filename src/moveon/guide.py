from __future__ import annotations

GUIDES: dict[str, str] = {
    "openai": """\
OpenAI / ChatGPT — request your data export

1. Open https://chatgpt.com
2. Click your profile picture (bottom left) → Settings
3. Choose "Data controls"
4. Click "Export data" → "Confirm export"
5. You receive an email with a download link (can take up to 24 hours)
6. Download the ZIP file

Expected file: a ZIP archive containing conversations.json and other files.

Then: moveon extract openai <downloaded-file.zip>
""",
    "anthropic": """\
Anthropic / Claude — request your data export

1. Open https://claude.ai
2. Click your profile picture → Settings
3. Choose "Account" → "Export Data"
4. Confirm the export
5. You receive an email with a download link
6. Download the ZIP file

Expected file: a ZIP archive containing your conversation data.

Then: moveon extract anthropic <downloaded-file.zip>
""",
    "google": """\
Google Gemini — export via Google Takeout

1. Open https://takeout.google.com
2. Click "Deselect all"
3. Scroll to "My Activity" and select only this product
4. Click "Multiple formats" → change the format from HTML to JSON
5. Click "Next step" → choose "Export once"
6. Choose ".zip" as file type and a suitable file size
7. Click "Create export"
8. You receive an email with a download link (can take a few hours)
9. Download the ZIP file

Expected file: takeout-YYYYMMDDTHHMMSS-001.zip
The relevant file is: Takeout/My Activity/Gemini Apps/MyActivity.json

Important: the format must be set to JSON (step 4); otherwise Google
exports the data as HTML.

Then: moveon extract google <downloaded-file.zip>
""",
    "meta": """\
Meta AI — request your data export

Option A: via Facebook "Download your information"
1. Open https://accountscenter.facebook.com/info_and_permissions/dyi
2. Choose "Download information"
3. Select the profile and "Select types of information"
4. Enable "Messages"
5. Choose "JSON" as format and the date range you want
6. Click "Submit request"
7. You receive a notification when the download is ready

Option B: via the Meta AI app
1. Open the Meta AI app or meta.ai
2. Go to Menu → Settings → Privacy and security
3. Choose "Manage your information" → "Download information"
4. Create the export in JSON format

Expected file: facebook-<username>-<date>.zip
Meta AI conversations are under: your_facebook_activity/messages/inbox/

Then: moveon extract meta <downloaded-file.zip>
""",
    "xai": """\
xAI / Grok — request your data export

1. Open https://grok.com
2. Click your profile picture → Settings → Data
3. Click "Export Data"
4. Alternatively: open https://accounts.x.ai/data → "Download account data"
5. You receive an email with a download link
6. Download the ZIP file

Expected file: a ZIP archive containing prod-grok-backend.json (conversations)
and other files (profile, billing, assets).

Then: moveon extract xai <downloaded-file.zip>
""",
    "mistral": """\
Mistral AI / Le Chat — request your data export

1. Open https://admin.mistral.ai/account/export
2. Click "Export"
3. The download starts automatically as a ZIP file

Expected file: a ZIP archive containing chat-{uuid}.json files (one per
conversation) and optional chat-{uuid}-files/ directories for attachments.

Note: conversations carry no title in the export — Move On uses the first
user message as the title.

Then: moveon extract mistral <downloaded-file.zip>
""",
    "perplexity": """\
Perplexity AI — request your data export

1. Open https://www.perplexity.ai
2. Click your profile picture → Settings → Account
3. Scroll to "Export Data" and click the button
4. Confirm the export
5. You receive an email with a download link (expires after 24 hours)
6. Download the ZIP file

Alternative: email privacy@perplexity.ai with the subject
"Data Export Request" (reply within 30 days).

Expected file: perplexity-data-export-YYYY-MM-DD.zip

Then: moveon extract perplexity <downloaded-file.zip>
""",
}


def get_guide(provider: str) -> str | None:
    return GUIDES.get(provider)


def list_providers() -> list[str]:
    return sorted(GUIDES.keys())

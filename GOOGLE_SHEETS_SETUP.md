# Google Sheets Setup Guide for FitKit Reviews

## Step 1: Create a Google Sheet

1. Go to [Google Sheets](https://sheets.google.com)
2. Create a new spreadsheet called "FitKit Reviews"
3. In the first row, add these headers:
   - A1: `Timestamp`
   - B1: `Email`
   - C1: `Gender`
   - D1: `Age`
   - E1: `Stars`
   - F1: `Review`

4. Copy the Sheet ID from the URL:
   - URL looks like: `https://docs.google.com/spreadsheets/d/SHEET_ID_HERE/edit`
   - Copy the `SHEET_ID_HERE` part

## Step 2: Create a Google Cloud Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Sheets API:
   - Go to "APIs & Services" → "Library"
   - Search for "Google Sheets API"
   - Click "Enable"
4. Enable the Google Drive API:
   - Search for "Google Drive API"
   - Click "Enable"

## Step 3: Create Service Account Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "Service Account"
3. Fill in the service account details:
   - Name: `fitkit-reviews`
   - Description: `Service account for FitKit review system`
4. Click "Create and Continue"
5. Skip the optional steps and click "Done"

## Step 4: Generate JSON Key

1. Click on the service account you just created
2. Go to the "Keys" tab
3. Click "Add Key" → "Create New Key"
4. Select "JSON" format
5. Click "Create" - this will download a JSON file

## Step 5: Share the Google Sheet

1. Open your Google Sheet
2. Click "Share" button
3. Add the service account email (found in the JSON file as `client_email`)
4. Give it "Editor" permissions
5. Click "Send"

## Step 6: Configure Streamlit Secrets

1. In your Streamlit Cloud app settings, go to "Secrets"
2. Add these secrets:

```toml
GOOGLE_SHEET_ID = "your-actual-sheet-id-here"
GOOGLE_SHEETS_CREDENTIALS = '''
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "your-private-key-id", 
  "private_key": "-----BEGIN PRIVATE KEY-----\nyour-actual-private-key\n-----END PRIVATE KEY-----\n",
  "client_email": "your-service-account@your-project.iam.gserviceaccount.com",
  "client_id": "your-client-id",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com"
}
'''
```

3. Replace all the placeholder values with the actual values from your downloaded JSON file

## Step 7: Test the Integration

1. Deploy your updated app
2. Generate a fitness plan
3. Leave a review - it should save to your Google Sheet!

## Data Structure

The Google Sheet will store:
- **Timestamp**: When the review was submitted
- **Email**: User's email address
- **Gender**: Male/Female/Other
- **Age**: User's age
- **Stars**: Rating from 1-5 stars
- **Review**: Text feedback from the user

## Troubleshooting

- Make sure the service account email has been added to the Google Sheet with Editor permissions
- Verify that both Google Sheets API and Google Drive API are enabled in your Google Cloud project
- Check that the JSON credentials are properly formatted in the secrets (no extra spaces or line breaks)
- The private key should include the `-----BEGIN PRIVATE KEY-----` and `-----END PRIVATE KEY-----` lines 
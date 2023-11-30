# File Storage Services

Docq supports multiple cloud file storage services as a data source. This section covers how to set up the supported file storage services.

## File storage: Google Drive

This guide aims to assist developers in integrating Google Drive with Docq. The focus will be on setting up the Google Drive API and obtaining the necessary credentials.

### Setup and configure Google Cloud project

- [Create a Google Cloud project](https://console.cloud.google.com/projectcreate) for your docq web application.
- [Enable the Google Drive API](https://console.cloud.google.com/flows/enableapi?apiid=drive.googleapis.com) in the project you just created.
- Goto Menu > APIs & Services > [OAuth consent screen](https://console.cloud.google.com/apis/credentials/consent) then click create and complete the App registration form with the following scopes:
  - `https://www.googleapis.com/auth/drive.readonly`
  - `https://www.googleapis.com/auth/userinfo.email`
  - `openid`
- Goto Menu > APIs & Services > [Credentials](https://console.cloud.google.com/apis/credentials) then click create credentials.
- Click `+ CREATE CREDENTIALS` > OAuth client ID then Fill the form with the following details:
  - Application type: Web application`
  - Authorized redirect URIs: `/Admin_Spaces/`, e.g. `https://localhost:5001/Admin_Spaces/`
- Click create and download the credentials.json file.
  
The more detailed guide can be found [here](https://developers.google.com/drive/api/quickstart/python).
  
### Configure Docq web application

After setting up the Google Cloud project and configuring the Google Drive API, you need to configure the Docq web application. This involves configuring the following environment variables:

- `DOCQ_GOOGLE_APPLICATION_CREDENTIALS`: The path to the credentials.json file.
- `DOCQ_GOOGLE_AUTH_REDIRECT_URL`: The redirect URL, e.g. `https://localhost:5001/Admin_Spaces/`. This must be an exact match to the Authorized redirect URIs in the Google Cloud Console.

Note: The Google drive data source will be automatically disabled if any of the above environment variables are not set.


## File storage: OneDrive

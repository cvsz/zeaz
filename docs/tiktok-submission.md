# TikTok Submission Notes

## Product and scope

- Product: Login Kit for Web
- Scope: `user.info.basic`
- Usage: The scope is used only to identify the signed-in TikTok account and connect it to the zTTShop workspace.
- Storage: OAuth tokens are stored encrypted on the server and used only for the authenticated session.
- Not used: Share Kit, Display API, Content Posting API, and any additional TikTok scopes are not part of this integration.

## Review text

zTTShop uses TikTok Login Kit for Web with the `user.info.basic` scope only. After the user authorizes the app, TikTok returns an authorization code to the approved callback URL, and the server exchanges it for encrypted access and refresh tokens. The app uses the returned account identity to connect the TikTok login to the workspace and support automation workflows. No posting, sharing, or profile display features are implemented in this integration.

## Demo video script

1. Open `https://zttshop.zeaz.dev/` and show the branded loading page.
2. Point out the visible TikTok Login Kit call to action and the live privacy and terms links.
3. Click the TikTok sign-in button and show the redirect to TikTok authorization.
4. Complete the authorization in the TikTok sandbox or review account.
5. Return to the callback URL and show the successful token exchange screen.
6. Show the connected account identifier and the confirmed `user.info.basic` scope.
7. Open the privacy page and terms page to show the published policy and usage rules.
8. End on the live hostname so the reviewer can verify the web domain matches the submission.

## Short prompt for a generated narration

Create a clean screen-recording style demo for a web app called zTTShop. Show the homepage, click the TikTok Login Kit button, complete the authorization flow, land on the callback success page, and then open the privacy and terms pages. The narration should explain that the app uses only `user.info.basic` to identify the TikTok account and store encrypted tokens for workflow automation. Do not mention unsupported products such as Share Kit, Display API, or Content Posting API.

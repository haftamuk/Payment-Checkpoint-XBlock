<!-- paymentcheckpoint/README.md -->

# Creating a new skeleton XBlock
cd /Users/macbookpro/openEdxProjects/xblock_development
xblock-sdk/bin/workbench-make-xblock

to install the package
pip install -e paymentcheckpoint


run it on xblock-sdk
cd /Users/macbookpro/openEdxProjects/xblock_development/xblock-sdk
python manage.py runserver 8882



# Payment Checkpoint XBlock

An Open edX XBlock that locks course content until a payment is made. After a successful payment (handled externally, e.g., by a WordPress/WooCommerce site), an API call marks the XBlock as complete. The block is designed to be used as a prerequisite for gated subsections.

## Overview

- **Learner view**: Displays a “Payment Required” message with a link to an external payment page. Once payment is confirmed, the content becomes accessible.
- **Studio configuration**: Course authors can set the payment URL (e.g., a WooCommerce product page).
- **API endpoint**: An external system (e.g., WordPress plugin) calls `/payment_checkpoint/mark_complete/` after payment, passing the username and XBlock usage key.
- **Authentication**: The endpoint is secured by Open edX’s platform-level JWT authentication – no API key inside the XBlock is required.

## Workflow

1. A learner reaches the Payment Checkpoint XBlock in the course.
2. The XBlock shows a link to the configured payment URL, including `username`, `course_id`, and `usage_id` as query parameters.
3. The learner pays on the external site (e.g., WordPress/WooCommerce).
4. After successful payment, the external site calls `https://<openedx-domain>/payment_checkpoint/mark_complete/` with a JSON body:
   ```json
   {
     "username": "learner_username",
     "usage_key": "block-v1:... (full usage key)"
   }
5. The XBlock’s complete flag is set to True and the CompletionService is updated, which unlocks any gated subsections that depend on this XBlock.

## Installation
### For development (XBlock SDK)
1. Clone the repository:
git clone git@github.com:haftamuk/Payment-Checkpoint-XBlock.git
cd Payment-Checkpoint-XBlock

2. Install the XBlock in editable mode:
pip install -e .

3. Run the XBlock SDK workbench:
cd /path/to/xblock-sdk
python manage.py runserver 8882

4. Open http://localhost:8882 and select the “PaymentCheckpointXBlock” scenario.

### For Open edX (Tutor)
1. Add the XBlock to your Tutor environment:

tutor plugins enable discovery

Or add the package directly to the requirements.txt of the openedx Docker image.

2. Install from the Git repository:

pip install git+https://github.com/haftamuk/Payment-Checkpoint-XBlock.git
(If using Tutor, you can do this in a custom Dockerfile or via tutor config save.)


3. Restart the LMS:
tutor local restart lms

4. Include the XBlock in a course:

Go to Studio → Course → Advanced Settings.

Add "paymentcheckpoint" to the Advanced Module List.

In a unit, click Add Component → Advanced → Payment Checkpoint.

5. Configure the XBlock in Studio:

Set the Payment URL (the link learners will be sent to for payment).

## Configuration
Field	Type	Description
payment_url	string	The URL of the payment page (e.g., WooCommerce product page).


## API Endpoint
URL: /payment_checkpoint/mark_complete/
Method: POST
Authentication: JWT (Bearer token) – the requesting client must have a valid token.
Request body (JSON):
{
  "username": "student_username",
  "usage_key": "block-v1:course+type+run+type@paymentcheckpoint+block@<id>"
}

Response:

200 OK: {"status": "ok"}

400/404/500: {"error": "description"}

Example with curl:

curl -X POST https://lms.example.com/payment_checkpoint/mark_complete/ \
  -H "Authorization: JWT <token>" \
  -H "Content-Type: application/json" \
  -d '{"username": "john", "usage_key": "block-v1:edX+DemoX+Demo_Course+type@paymentcheckpoint+block@abc123"}'


## Testing in the XBlock SDK
The workbench includes a “Simulate Payment” button that directly marks the XBlock as complete – no external call is needed. This is useful for testing the unlock behaviour.

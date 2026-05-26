
<!-- paymentcheckpoint/README.md -->


Now that your XBlock is successfully installed and registered (the entry point `paymentcheckpoint` appears in the list), the final step is to enable it for your course in **Studio**. Below is the complete, step‑by‑step command guide to see the XBlock in your **Open edX Tutor development environment**.

## Complete workflow to see PaymentCheckpointXBlock in Studio

### 1. Ensure the XBlock is installed (you already did this)
```bash
# Enter the CMS container and manually install the XBlock (if not present)
tutor dev exec cms bash
pip install git+https://github.com/haftamuk/Payment-Checkpoint-XBlock.git@main
exit
tutor dev restart cms
```

### 2. Verify the XBlock entry point is registered
```bash
tutor dev exec cms python -c "from pkg_resources import iter_entry_points; print([ep.name for ep in iter_entry_points('xblock.v1')])" | grep paymentcheckpoint
```
You should see `'paymentcheckpoint'` in the output.

### 3. Enable the XBlock in your course (Studio configuration)
- Open your course in **Studio** (e.g., `https://studio.local.openedx.io/course/course-v1:…`)
- Go to **Settings** → **Advanced Settings**
- Find the field **Advanced Module List**
- Add `"paymentcheckpoint"` to the list. For example:
  ```json
  ["paymentcheckpoint", "other_blocks"]
  ```
- Click **Save Changes**

### 4. Add the XBlock to a unit
- Navigate to **Content** → **Outline** and select a **Section** and **Subsection** where you want the checkpoint.
- Under an existing **Unit**, click **Add New Component** → **Advanced** → **Payment Checkpoint**.
- The XBlock will appear in the unit.

### 5. (Optional) Test the XBlock locally
- In the LMS (learner view), the block will show a **Proceed to Payment** link.
- Use the **Simulate Payment** button (visible only in the SDK) to test the completion flow without a real payment service.

## Notes for development
- If you later update the XBlock code, re‑install it inside the container:
  ```bash
  tutor dev exec cms bash
  pip uninstall paymentcheckpoint-xblock -y
  pip install git+https://github.com/haftamuk/Payment-Checkpoint-XBlock.git@main
  exit
  tutor dev restart cms
  ```
- For faster iteration during development, use **editable installation**:
  ```bash
  # Clone the repo on your host, then mount it
  tutor mounts add /path/to/Payment-Checkpoint-XBlock
  tutor dev launch
  ```

Now the XBlock should appear in your Studio component list. If it still does not show, double‑check that the course’s **Advanced Module List** includes exactly `"paymentcheckpoint"` (including the quotes) and that you have saved the changes.



# Creating a new skeleton XBlock
cd /Users/macbookpro/openEdxProjects/xblock_development
xblock-sdk/bin/workbench-make-xblock

to install the package
(venv) macbookpro@MacBooks-MacBook-Pro xblock_development % cd xblock-sdk 
pip uninstall paymentcheckpoint-xblock
pip install -e ../payment-checkpoint-xblock 


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

/Users/macbookpro/Library/Application Support/tutor-main
tutor config save
tutor restart restart lms

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

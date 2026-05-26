"""PaymentCheckpointXBlock – Protects course content until payment is made."""

import logging
from pathlib import Path

from web_fragments.fragment import Fragment
from xblock.core import XBlock
from xblock.fields import Scope, Boolean, String

logger = logging.getLogger(__name__)


class PaymentCheckpointXBlock(XBlock):
    """
    XBlock that shows a payment gate. After a successful payment, an external
    API (e.g., a WordPress plugin) marks this block as complete.
    """

    has_completion = True
    has_score = False
    show_in_read_only_mode = True

    # Student state
    complete = Boolean(
        default=False,
        scope=Scope.user_state,
        help="Whether the student has completed payment for this checkpoint."
    )

    # Course settings (editable in Studio)
    payment_url = String(
        default="https://your-wordpress-site.com/course-product/",
        scope=Scope.settings,
        help="URL of the WooCommerce product page (the payment link)."
    )

    def _get_student_username(self):
        """Return the current username, or 'testuser' in the workbench."""
        try:
            user_service = self.runtime.service(self, 'user')
            if user_service:
                user = user_service.get_current_user()
                return user.opt_attrs.get('username', 'testuser')
        except Exception:
            pass
        return 'testuser'

    def resource_string(self, path):
        """Load a file from the static directory."""
        return (Path(__file__).parent / 'static' / path).read_text(encoding='utf-8')

    def student_view(self, context=None):
        """Main view shown to learners."""
        username = self._get_student_username()
        course_id = str(getattr(self, 'course_id', 'course-v1:test+test+2024'))
        usage_id = str(self.scope_ids.usage_id)

        # Load CSS and JS as inline strings
        css_content = self.resource_string('css/paymentcheckpoint.css')
        js_content = self.resource_string('js/paymentcheckpoint.js')

        if self.complete:
            inner_html = """
                <div class="payment-success">
                    <h3>🎉 Payment Confirmed</h3>
                    <p>You have successfully unlocked this course content.</p>
                </div>
            """
        else:
            inner_html = f"""
                <div class="payment-required">
                    <h3>🔒 Payment Required</h3>
                    <p>You need to make a payment to access the rest of this course.</p>
                    <a class="payment-button"
                       href="{self.payment_url}?username={username}&course_id={course_id}&usage_id={usage_id}"
                       target="_blank">
                        Proceed to Payment
                    </a>
                    <hr />
                    <button id="simulate-payment-btn" style="margin-top:1rem; padding:8px 16px;">🔧 Simulate Payment (SDK only)</button>
                </div>
            """

        outer_template = self.resource_string('html/paymentcheckpoint.html')
        html_content = outer_template.format(content=inner_html)

        frag = Fragment(html_content)
        frag.add_css(css_content)
        frag.add_javascript(js_content)
        frag.initialize_js('PaymentCheckpointXBlock')
        return frag

    def author_view(self, context=None):
        """
        Render a placeholder in Studio – the actual configuration is done via the
        edit button (which opens studio_view).
        """
        html = """
            <div class="payment-checkpoint-author-view">
                <p>🔒 <strong>Payment Checkpoint</strong></p>
                <p>This block protects content until a payment is made.</p>
                <p>Configure the <strong>Payment URL</strong> using the edit button (pencil icon).</p>
            </div>
        """
        frag = Fragment(html)
        # No CSS/JS needed for the author view
        return frag

    @XBlock.handler
    def simulate_paid(self, request, suffix=''):
        """Testing handler – marks the block as complete without external call."""
        self.complete = True
        return {'status': 'ok', 'complete': True}

    def studio_view(self, context=None):
        """Studio configuration view – only the payment URL is editable."""
        from django.utils.html import format_html
        html = format_html(
            '<div class="wrapper-comp-settings">'
            '<p>Payment URL: <input type="text" name="payment_url" value="{payment_url}" style="width:100%"/></p>'
            '</div>',
            payment_url=self.payment_url,
        )
        frag = Fragment(html)
        frag.add_javascript("""
            function PaymentCheckpointStudioXBlock(runtime, element) {
                $('.save-button', element).click(function() {
                    var data = {
                        'payment_url': $('input[name=payment_url]', element).val()
                    };
                    runtime.notify('save', {state: 'start'});
                    $.ajax({
                        type: 'POST',
                        url: runtime.handlerUrl(element, 'studio_submit'),
                        data: JSON.stringify(data),
                        success: function() { runtime.notify('save', {state: 'end'}); }
                    });
                });
            }
        """)
        frag.initialize_js('PaymentCheckpointStudioXBlock')
        return frag

    @XBlock.handler
    def studio_submit(self, request, suffix=''):
        """Handle Studio settings submission."""
        import json
        data = json.loads(request.body)
        self.payment_url = data.get('payment_url', self.payment_url)
        return {'result': 'success'}

    @staticmethod
    def workbench_scenarios():
        """Scenarios for testing in the XBlock SDK."""
        return [
            ("PaymentCheckpointXBlock",
             """<paymentcheckpoint/>"""),
            ("Multiple PaymentCheckpointXBlock",
             """<vertical_demo>
                <paymentcheckpoint/>
                <paymentcheckpoint/>
                <paymentcheckpoint/>
                </vertical_demo>"""),
        ]
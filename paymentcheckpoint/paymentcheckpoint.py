"""PaymentCheckpointXBlock – Protects course content until payment is made."""

import json
import logging
from pathlib import Path

from web_fragments.fragment import Fragment
from webob import Response
from xblock.core import XBlock
from xblock.fields import Scope, Boolean, String

logger = logging.getLogger(__name__)


class PaymentCheckpointXBlock(XBlock):
    has_completion = True
    has_score = False
    show_in_read_only_mode = True

    complete = Boolean(default=False, scope=Scope.user_state)
    payment_url = String(
        default="https://your-wordpress-site.com/course-product/",
        scope=Scope.settings,
    )
    display_name = String(default="Payment Checkpoint", scope=Scope.settings)

    def resource_string(self, path):
        return (Path(__file__).parent / 'static' / path).read_text(encoding='utf-8')

    def student_view(self, context=None):
        # Studio preview mode – show a safe placeholder without any JS/CSS
        if context and context.get('is_author_mode'):
            usage_id = str(self.scope_ids.usage_id)
            html = f'''
                <div class="payment-checkpoint-placeholder" data-usage-id="{usage_id}">
                    <p>🔒 <strong>Payment Checkpoint</strong></p>
                    <p>Configure the Payment URL using the Edit button.</p>
                </div>
            '''
            return Fragment(html)

        # Normal learner view
        username = self._get_student_username()
        course_id = str(getattr(self, 'course_id', 'course-v1:test+test+2024'))
        usage_id = str(self.scope_ids.usage_id)

        css_content = self.resource_string('css/paymentcheckpoint.css')
        js_content = self.resource_string('js/paymentcheckpoint.js')

        if self.complete:
            inner_html = '''
                <div class="payment-success">
                    <h3>🎉 Payment Confirmed</h3>
                    <p>You have successfully unlocked this course content.</p>
                </div>
            '''
        else:
            inner_html = f'''
                <div class="payment-required">
                    <h3>🔒 Payment Required</h3>
                    <p>You need to make a payment to access the rest of this course.</p>
                    <a class="payment-button"
                       href="{self.payment_url}?username={username}&course_id={course_id}&usage_id={usage_id}"
                       target="_blank">
                        Proceed to Payment
                    </a>
                </div>
            '''

        outer_template = self.resource_string('html/paymentcheckpoint.html')
        html_content = outer_template.format(content=inner_html, usage_id=usage_id)

        frag = Fragment(html_content)
        frag.add_css(css_content)
        frag.add_javascript(js_content)
        frag.initialize_js('PaymentCheckpointXBlock')
        return frag

    def studio_view(self, context=None):
        """Custom editing view for Studio – input field is fully responsive."""
        from django.utils.html import format_html

        html = format_html(
            '<div class="wrapper-comp-settings" style="min-width: 260px;">'
            '<fieldset class="list-input">'
            '<div class="field comp-setting-entry">'
            '<label class="label setting-label" for="payment_url">Payment URL</label>'
            '<input type="text" id="payment_url" name="payment_url" '
            'value="{payment_url}" style="width: 100%; box-sizing: border-box;">'
            '</div>'
            '</fieldset>'
            '</div>'
            '<div class="xblock-actions">'
            '<button class="button action-save">Save</button>'
            '<button class="button action-cancel">Cancel</button>'
            '</div>',
            payment_url=self.payment_url,
        )
        frag = Fragment(html)
        frag.add_javascript("""
            function PaymentCheckpointStudioXBlock(runtime, element) {
                $('.action-save', element).click(function() {
                    var data = {
                        'payment_url': $('#payment_url', element).val()
                    };
                    runtime.notify('save', {state: 'start'});
                    $.ajax({
                        type: 'POST',
                        url: runtime.handlerUrl(element, 'studio_submit'),
                        data: JSON.stringify(data),
                        contentType: 'application/json',
                        success: function() {
                            runtime.notify('save', {state: 'end'});
                        },
                        error: function() {
                            runtime.notify('error', {msg: 'Save failed. Please try again.'});
                        }
                    });
                });
                $('.action-cancel', element).click(function() {
                    runtime.notify('cancel', {});
                });
            }
        """)
        frag.initialize_js('PaymentCheckpointStudioXBlock')
        return frag

    @XBlock.handler
    def studio_submit(self, request, suffix=''):
        """Handle Studio settings submission – returns proper WebOb Response."""
        try:
            data = json.loads(request.body)
            self.payment_url = data.get('payment_url', self.payment_url)
            # Return a JSON response with charset
            return Response(
                body=json.dumps({'result': 'success'}),
                content_type='application/json',
                charset='utf-8',
                status=200
            )
        except Exception as e:
            logger.exception("Studio submit failed")
            return Response(
                body=json.dumps({'error': str(e)}),
                content_type='application/json',
                charset='utf-8',
                status=500
            )

    def _get_student_username(self):
        try:
            user_service = self.runtime.service(self, 'user')
            if user_service:
                user = user_service.get_current_user()
                return user.opt_attrs.get('username', 'testuser')
        except Exception:
            pass
        return 'testuser'

    @XBlock.handler
    def simulate_paid(self, request, suffix=''):
        self.complete = True
        return Response(
            body=json.dumps({'status': 'ok', 'complete': True}),
            content_type='application/json',
            charset='utf-8',
            status=200
        )

    @staticmethod
    def workbench_scenarios():
        return [
            ("PaymentCheckpointXBlock", """<paymentcheckpoint/>"""),
        ]
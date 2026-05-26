// paymentcheckpoint/paymentcheckpoint/static/js/paymentcheckpoint.js
function PaymentCheckpointXBlock(runtime, element) {
    var simulateBtn = $('#simulate-payment-btn', element);
    if (simulateBtn.length) {
        simulateBtn.click(function() {
            var handlerUrl = runtime.handlerUrl(element, 'simulate_paid');
            $.ajax({
                type: 'POST',
                url: handlerUrl,
                success: function(response) {
                    if (response.complete) {
                        location.reload();  // Reload to show success state
                    }
                }
            });
        });
    }
}
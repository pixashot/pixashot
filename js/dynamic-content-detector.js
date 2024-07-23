// File: dynamic-content-detector.js

window.detectDynamicContentLoading = function(checkInterval = 1000, maxUnchangedChecks = 5) {
    return new Promise((resolve) => {
        let lastDocumentHeight = document.body.scrollHeight;
        let unchangedCounter = 0;

        function checkDynamicContent() {
            let currentHeight = document.body.scrollHeight;
            if (currentHeight === lastDocumentHeight) {
                unchangedCounter++;
                if (unchangedCounter >= maxUnchangedChecks) {
                    resolve();
                    return;
                }
            } else {
                unchangedCounter = 0;
                lastDocumentHeight = currentHeight;
            }
            setTimeout(checkDynamicContent, checkInterval);
        }

        checkDynamicContent();
    });
};
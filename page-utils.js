// Disable smooth scrolling
function disableSmoothScrolling() {
    const style = document.createElement('style');
    style.innerHTML = `* { scroll-behavior: auto !important; }`;
    document.head.appendChild(style);
}

// Wait for all images to load, including dynamically added ones
function waitForAllImages() {
    return new Promise((resolve) => {
        let images = Array.from(document.images);
        let loadedImages = 0;

        function checkAllImagesLoaded() {
            loadedImages++;
            if (loadedImages === images.length) {
                resolve();
            }
        }

        images.forEach(img => {
            if (img.complete) {
                checkAllImagesLoaded();
            } else {
                img.onload = img.onerror = checkAllImagesLoaded;
            }
        });

        // Handle dynamically added images
        const observer = new MutationObserver(mutations => {
            mutations.forEach(mutation => {
                mutation.addedNodes.forEach(node => {
                    if (node.nodeName.toLowerCase() === 'img') {
                        images.push(node);
                        if (node.complete) {
                            checkAllImagesLoaded();
                        } else {
                            node.onload = node.onerror = checkAllImagesLoaded;
                        }
                    }
                });
            });
        });

        observer.observe(document.body, { childList: true, subtree: true });

        // Resolve after a timeout if not all images load
        setTimeout(resolve, 30000);
    });
}

// Get the full height of the page
function getFullHeight() {
    return document.body.scrollHeight;
}

// Expose functions to be called from Python
window.pageUtils = {
    disableSmoothScrolling,
    waitForAllImages,
    getFullHeight
};
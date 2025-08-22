document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('conversionForm');
    const loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'));
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const youtubeUrl = document.getElementById('youtubeUrl').value;
        
        if (!youtubeUrl) {
            alert('Please enter a YouTube URL');
            return;
        }
        
        // Show loading modal
        loadingModal.show();
        
        // Send request to process the video
        fetch('/process', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `youtube_url=${encodeURIComponent(youtubeUrl)}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.task_id) {
                // Redirect to loading page
                window.location.href = `/loading/${data.task_id}`;
            } else if (data.error) {
                loadingModal.hide();
                alert('Error: ' + data.error);
            }
        })
        .catch(error => {
            loadingModal.hide();
            console.error('Error:', error);
            alert('An error occurred while processing your request');
        });
    });
});
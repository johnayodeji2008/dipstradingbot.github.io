
document.addEventListener("DOMContentLoaded", () => {
    const preloader = document.getElementById("preloader");
    const mainContent = document.getElementById("main-content");
    const loadingAnimation = document.getElementById("loading-animation");
    const signalData = document.getElementById("signal-data");
    const refreshButton = document.getElementById("refresh-button");

    // Hide preloader and show main content
    setTimeout(() => {
        preloader.style.display = "none";
        mainContent.classList.remove("hidden");
        setTimeout(() => mainContent.classList.add("loaded"), 100);
        fetchSignal();
    }, 2000);

    // Function to fetch signal from server
    function fetchSignal() {
        loadingAnimation.classList.remove("hidden");
        signalData.classList.add("hidden");

        fetch('/get_signal')
            .then(response => response.json())
            .then(data => {
                loadingAnimation.classList.add("hidden");
                if (data.error) {
                    alert(`Error: ${data.error}`);
                } else {
                    document.getElementById("entry-point").textContent = data.entry;
                    document.getElementById("take-profit").textContent = data.take_profit;
                    document.getElementById("stop-loss").textContent = data.stop_loss;
                    document.getElementById("risk-reward").textContent = data.risk_to_reward.toFixed(2);
                    signalData.classList.remove("hidden");
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while fetching the signal.');
            });
    }

    // Refresh button event listener
    refreshButton.addEventListener("click", fetchSignal);
});

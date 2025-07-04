document.addEventListener("DOMContentLoaded", function() {
    const whisperButton = document.getElementById("whisper-mode");
    const wordstoryButton = document.getElementById("wordstory-mode");
    const whisperInterface = document.getElementById("whisper-interface");
    const vocabularyInterface = document.getElementById("vocabulary-interface");

    whisperButton.addEventListener("click", function() {
        whisperInterface.style.display = "block";
        vocabularyInterface.style.display = "none";
    });

    wordstoryButton.addEventListener("click", function() {
        vocabularyInterface.style.display = "block";
        whisperInterface.style.display = "none";
    });

    // Initialize the interface to show the main menu
    whisperInterface.style.display = "none";
    vocabularyInterface.style.display = "none";
});
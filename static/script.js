// Toggle Password Visibility
function togglePassword(inputId) {
    let passwordField = document.getElementById(inputId);
    passwordField.type = passwordField.type === "password" ? "text" : "password";
}

// Signup Form Submission
document.getElementById("signup-form").addEventListener("submit", function(event) {
    event.preventDefault();
    let formData = new FormData(this);

    fetch("/signup", {
        method: "POST",
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.href = data.redirect;
        } else {
            alert("Signup failed: " + data.message);
        }
    })
    .catch(error => console.error("Error:", error));
});

// Login Form Submission
document.getElementById("login-form").addEventListener("submit", function(event) {
    event.preventDefault();
    let formData = new FormData(this);

    fetch("/login", {
        method: "POST",
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.href = data.redirect;
        } else {
            alert("Login failed: " + data.message);
        }
    })
    .catch(error => console.error("Error:", error));
});

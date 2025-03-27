const container = document.getElementById('container');
const registerBtn = document.getElementById('register');
const loginBtn = document.getElementById('login');

registerBtn.addEventListener('click', () => {
    container.classList.add("active");
});

loginBtn.addEventListener('click', () => {
    container.classList.remove("active");
});

//Registeration
document.querySelector(".sign-up form").addEventListener("submit", async function(event) {
    event.preventDefault(); // Prevent page reload

    // Get form values
    const name = document.querySelector(".sign-up input[placeholder='Name']").value;
    const email = document.querySelector(".sign-up input[placeholder='Email']").value;
    const password = document.querySelector(".sign-up input[placeholder='Password']").value;
    const userType = document.querySelector(".sign-up input[name='userType']:checked")?.value;

    if (!userType) {
        alert("Please select if you are a Donor or Recipient.");
        return;
    }

    try {
        // Step 1: Check if user already exists
        const checkResponse = await fetch(`http://127.0.0.1:8000/user_exists?email=${encodeURIComponent(email)}`);
        const checkData = await checkResponse.json();

        if (checkResponse.ok && checkData.exists) {
            alert("User with this email already exists. Please use a different email.");
            return;
        }

        // Step 2: Register User (Only if email is unique)
        const response = await fetch("http://127.0.0.1:8000/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, email, password }) // Send only essential user data
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Registration failed");
        }

        alert("User registered successfully!");

        // Redirect to the appropriate form based on userType
        const redirectURL = userType === "donor"
            ? `../SETUPDONOR/set.html?email=${encodeURIComponent(email)}`
            : `../SETUPEME/setupr.html?email=${encodeURIComponent(email)}`;

        window.location.href = redirectURL;
        
    } catch (error) {
        alert("Error: " + error.message);
    }
});

//login
document.querySelector(".sign-in button").addEventListener("click", async function(event) {
    event.preventDefault(); // Prevent page reload

    // Get form values
    const email = document.querySelector(".sign-in input[placeholder='Email']").value;
    const password = document.querySelector(".sign-in input[placeholder='Password']").value;

    if (!email || !password) {
        alert("Please enter both email and password.");
        return;
    }

    try {
        // Step 1: Check if user exists
        const checkResponse = await fetch(`http://127.0.0.1:8000/user_exists?email=${encodeURIComponent(email)}`);
        const checkData = await checkResponse.json();

        if (!checkResponse.ok || !checkData.exists) {
            alert("No account found with this email. Please register first.");
            return;
        }

        // Step 2: Log in the user
        const response = await fetch("http://127.0.0.1:8000/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Invalid email or password.");
        }

        alert("Login successful!");

        // Step 3: Redirect to main dashboard
        window.location.href = "../dasHbOArd/db.html?email=" + encodeURIComponent(email);
        
    } catch (error) {
        alert("Error: " + error.message);
    }
});

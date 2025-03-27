document.addEventListener("DOMContentLoaded", () => {
    // Get email from URL parameters
    const urlParams = new URLSearchParams(window.location.search)
    const email = urlParams.get("email")
  
    if (!email) {
      alert("Email parameter is missing. Please go back to the registration page.")
      window.location.href = "../lOgIn/sign.html"
      return
    }
  
    // Add a hidden email field to the form
    const emailInput = document.createElement("input")
    emailInput.type = "hidden"
    emailInput.name = "email"
    emailInput.value = email
    document.querySelector("form").appendChild(emailInput)
  
    // Handle form submission
    document.querySelector("form").addEventListener("submit", async function (event) {
      event.preventDefault()
  
      // Collect all form data
      const formData = new FormData(this)
      const formDataObj = {}
  
      formData.forEach((value, key) => {
        formDataObj[key] = value
      })
  
      try {
        // Submit donor form data
        const response = await fetch("http://127.0.0.1:8000/submit-donor-form", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(formDataObj),
        })
  
        const data = await response.json()
  
        if (!response.ok) {
          throw new Error(data.detail || "Failed to submit donor form")
        }
  
        alert("Donor form submitted successfully!")
  
        // Redirect to dashboard
        window.location.href = `../dasHbOArd/db.html?email=${encodeURIComponent(email)}`
      } catch (error) {
        alert("Error: " + error.message)
      }
    })
  })
  
  async function submitEmergencyContacts(userId, contacts) {
    try {
      const response = await fetch(`http://127.0.0.1:8000/add-emergency-contacts/${userId}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(contacts),
      })
  
      const data = await response.json()
  
      if (!response.ok) {
        throw new Error(data.detail || "Failed to add emergency contacts")
      }
  
      return data
    } catch (error) {
      throw error
    }
  }
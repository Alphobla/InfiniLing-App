// Custom Cypress commands

// Login with email and password
Cypress.Commands.add('login', (email, password) => {
  cy.visit('/login')
  cy.get('input[type="email"]').type(email)
  cy.get('input[type="password"]').type(password)
  cy.get('button[type="submit"]').click()
  cy.url().should('not.include', '/login', { timeout: 10000 })
})

// Login with the dedicated test user (expects user to have settings already)
Cypress.Commands.add('loginTestUser', () => {
  cy.fixture('test-data').then((data) => {
    cy.login(data.testUser.email, data.testUser.password)
    // Wait for redirect - could be dashboard or onboarding
    cy.url({ timeout: 10000 }).then((url) => {
      if (url.includes('/onboarding')) {
        // Complete onboarding if settings don't exist
        cy.completeOnboarding()
      }
    })
    // Ensure we end up on dashboard
    cy.url().should('eq', Cypress.config().baseUrl + '/', { timeout: 10000 })
  })
})

// Complete onboarding flow (assumes already on /onboarding page)
Cypress.Commands.add('completeOnboarding', () => {
  cy.url().should('include', '/onboarding')
  cy.get('select').select('English')
  cy.contains('button', 'Continue').click()
  cy.contains('button', 'Get Started', { timeout: 5000 }).click()
  cy.url().should('eq', Cypress.config().baseUrl + '/', { timeout: 10000 })
})

// Sign up a new user with unique email
Cypress.Commands.add('signupNewUser', () => {
  cy.fixture('test-data').then((data) => {
    const uniqueEmail = `${data.newUser.emailPrefix}-${Date.now()}@test.com`
    cy.visit('/signup')
    cy.get('input[type="email"]').type(uniqueEmail)
    cy.get('input[type="password"]').type(data.newUser.password)
    cy.get('button[type="submit"]').click()
    cy.wrap(uniqueEmail).as('newUserEmail')
  })
})

// Add a vocabulary word
Cypress.Commands.add('addWord', (word, translation) => {
  cy.visit('/vocabulary')
  cy.contains('button', /add/i).click()
  cy.get('input[placeholder*="word" i], input[name="word"]').type(word)
  cy.get('input[placeholder*="translation" i], input[name="translation"]').type(translation)
  cy.get('form').contains('button', /add|save|submit/i).click()
})

// Ensure we're logged in before test (for tests that need auth)
Cypress.Commands.add('ensureLoggedIn', () => {
  cy.visit('/')
  cy.url().then((url) => {
    if (url.includes('/login')) {
      cy.loginTestUser()
    } else if (url.includes('/onboarding')) {
      // User is logged in but needs to complete onboarding
      cy.completeOnboarding()
    }
  })
})

// Wait for API call to complete
Cypress.Commands.add('waitForApi', (method, route) => {
  cy.intercept(method, route).as('apiCall')
  cy.wait('@apiCall')
})

// Logout
Cypress.Commands.add('logout', () => {
  cy.contains(/sign out|logout/i).click()
  cy.url().should('include', '/login')
})

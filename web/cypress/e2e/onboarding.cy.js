describe('Onboarding', () => {
  it('should complete onboarding flow', () => {
    const uniqueEmail = `onboard-${Date.now()}@test.com`

    cy.visit('/signup')
    cy.get('input[type="email"]').type(uniqueEmail)
    cy.get('input[type="password"]').type('TestPassword123!')
    cy.get('button[type="submit"]').click()

    // Should be on onboarding page
    cy.url().should('include', '/onboarding', { timeout: 15000 })

    // Step 1: Select mother tongue
    cy.get('select').select('English')
    cy.contains('button', 'Continue').click()

    // Step 2: See intro - check for actual text from Onboarding.jsx
    cy.contains("You're all set", { timeout: 5000 }).should('be.visible')
    cy.contains('button', 'Get Started').click()

    // Should redirect to dashboard
    cy.url().should('eq', Cypress.config().baseUrl + '/', { timeout: 10000 })
  })

  it('should redirect to onboarding if user has no settings', () => {
    // Create a new user that hasn't completed onboarding
    const uniqueEmail = `nosetup-${Date.now()}@test.com`

    cy.visit('/signup')
    cy.get('input[type="email"]').type(uniqueEmail)
    cy.get('input[type="password"]').type('TestPassword123!')
    cy.get('button[type="submit"]').click()

    // Should be redirected to onboarding
    cy.url().should('include', '/onboarding', { timeout: 15000 })
    cy.contains('Welcome to InfiniLing').should('be.visible')
    cy.get('select').should('be.visible')
  })

  it('should redirect to dashboard if user already has settings', () => {
    // Login with test user who should have settings
    cy.loginTestUser()

    // Try to visit onboarding - should redirect to dashboard
    cy.visit('/onboarding')
    cy.url().should('eq', Cypress.config().baseUrl + '/', { timeout: 10000 })
  })

  it('should redirect to login if not authenticated', () => {
    // Clear any existing session
    cy.clearCookies()
    cy.clearLocalStorage()

    // Try to visit onboarding without being logged in
    cy.visit('/onboarding')
    cy.url().should('include', '/login', { timeout: 10000 })
  })
})

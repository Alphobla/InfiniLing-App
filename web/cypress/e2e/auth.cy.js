describe('Authentication', () => {
  beforeEach(() => {
    cy.visit('/login')
  })

  it('should sign up a new user', () => {
    const uniqueEmail = `newuser-${Date.now()}@test.com`

    cy.visit('/signup')
    cy.get('input[type="email"]').type(uniqueEmail)
    cy.get('input[type="password"]').type('TestPassword123!')
    cy.get('button[type="submit"]').click()

    // Should redirect to onboarding after signup
    cy.url().should('include', '/onboarding', { timeout: 10000 })
  })

  it('should login with valid credentials', () => {
    cy.fixture('test-data').then((data) => {
      cy.get('input[type="email"]').type(data.testUser.email)
      cy.get('input[type="password"]').type(data.testUser.password)
      cy.get('button[type="submit"]').click()

      // Wait for redirect - could be dashboard or onboarding
      cy.url().should('not.include', '/login', { timeout: 10000 })

      // Handle onboarding if needed, then verify dashboard
      cy.url().then((url) => {
        if (url.includes('/onboarding')) {
          // User doesn't have settings yet - complete onboarding
          cy.get('select').select('English')
          cy.contains('button', 'Continue').click()
          cy.contains('button', 'Get Started', { timeout: 5000 }).click()
        }
      })

      // Should be on dashboard after login (or after onboarding)
      cy.url().should('eq', Cypress.config().baseUrl + '/', { timeout: 15000 })
      cy.contains(/welcome|dashboard/i).should('be.visible')
    })
  })

  it('should logout', () => {
    // Login first
    cy.loginTestUser()

    // Wait for dashboard to load
    cy.url().should('eq', Cypress.config().baseUrl + '/')

    // Click logout
    cy.contains(/sign out|logout/i).click()

    // Should redirect to login page
    cy.url().should('include', '/login')
  })
})

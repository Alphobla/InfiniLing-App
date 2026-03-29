describe('Onboarding', () => {
  it('should complete onboarding via Start Fresh path', () => {
    const uniqueEmail = `onboard-fresh-${Date.now()}@test.com`

    cy.visit('/signup')
    cy.get('input[type="email"]').type(uniqueEmail)
    cy.get('input[type="password"]').type('TestPassword123!')
    cy.get('button[type="submit"]').click()

    // Should be on onboarding page
    cy.url().should('include', '/onboarding', { timeout: 15000 })

    // Screen 1: Select both languages
    cy.contains('Select your languages').should('be.visible')
    cy.get('select').first().select('English')      // I speak
    cy.get('select').last().select('Spanish')        // I want to learn
    cy.contains('button', 'Continue').click()

    // Screen 2: Choose path
    cy.contains('How would you like to start?', { timeout: 5000 }).should('be.visible')
    cy.contains('Start Fresh').click()

    // Should redirect to vocabulary page
    cy.url().should('include', '/vocabulary', { timeout: 10000 })
  })

  it('should complete onboarding via Pick Unknown Words path', () => {
    const uniqueEmail = `onboard-pick-${Date.now()}@test.com`

    cy.visit('/signup')
    cy.get('input[type="email"]').type(uniqueEmail)
    cy.get('input[type="password"]').type('TestPassword123!')
    cy.get('button[type="submit"]').click()

    cy.url().should('include', '/onboarding', { timeout: 15000 })

    // Screen 1
    cy.get('select').first().select('German')
    cy.get('select').last().select('French')
    cy.contains('button', 'Continue').click()

    // Screen 2
    cy.contains('Pick Unknown Words', { timeout: 5000 }).click()

    // Screen 3a: Word Picker
    cy.contains('Pick 10 unknown words', { timeout: 5000 }).should('be.visible')
    cy.contains('0 / 10 selected').should('be.visible')

    // Select 10 words (click first 10 word buttons in the scrollable list)
    cy.get('[class*="rounded-lg"]').filter(':contains("")').then($words => {
      for (let i = 0; i < 10; i++) {
        cy.wrap($words[i]).click()
      }
    })

    cy.contains('10 / 10 selected').should('be.visible')
    cy.contains('button', 'Continue').click()

    // Should redirect to vocabulary page
    cy.url().should('include', '/vocabulary', { timeout: 10000 })
  })

  it('should redirect to onboarding if user has no settings', () => {
    const uniqueEmail = `nosetup-${Date.now()}@test.com`

    cy.visit('/signup')
    cy.get('input[type="email"]').type(uniqueEmail)
    cy.get('input[type="password"]').type('TestPassword123!')
    cy.get('button[type="submit"]').click()

    cy.url().should('include', '/onboarding', { timeout: 15000 })
    cy.contains('Select your languages').should('be.visible')
  })

  it('should redirect to dashboard if user already has settings', () => {
    cy.loginTestUser()
    cy.visit('/onboarding')
    cy.url().should('eq', Cypress.config().baseUrl + '/', { timeout: 10000 })
  })

  it('should redirect to login if not authenticated', () => {
    cy.clearCookies()
    cy.clearLocalStorage()
    cy.visit('/onboarding')
    cy.url().should('include', '/login', { timeout: 10000 })
  })

  it('should navigate back from Screen 2 to Screen 1', () => {
    const uniqueEmail = `onboard-back-${Date.now()}@test.com`

    cy.visit('/signup')
    cy.get('input[type="email"]').type(uniqueEmail)
    cy.get('input[type="password"]').type('TestPassword123!')
    cy.get('button[type="submit"]').click()

    cy.url().should('include', '/onboarding', { timeout: 15000 })

    // Complete Screen 1
    cy.get('select').first().select('English')
    cy.get('select').last().select('German')
    cy.contains('button', 'Continue').click()

    // On Screen 2, click Back
    cy.contains('How would you like to start?', { timeout: 5000 }).should('be.visible')
    cy.contains('Back').click()

    // Back on Screen 1
    cy.contains('Select your languages').should('be.visible')
  })
})

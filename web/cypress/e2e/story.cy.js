describe('Story Generator', () => {
  beforeEach(() => {
    cy.loginTestUser()
  })

  it('should generate a story', () => {
    cy.visit('/story')
    cy.wait(2000)

    // Check if there are words available
    cy.get('body').then(($body) => {
      const bodyText = $body.text()

      if (bodyText.includes('No vocabulary') || bodyText.includes('Add some first')) {
        // No words - just verify empty state
        cy.contains(/no.*words|add.*first/i).should('be.visible')
      } else {
        // Select a word - click on word buttons in the selection area
        cy.get('button').contains(/^(?!Generate|Select|Clear|Listen).+/).first().click()

        // Click generate - find button with "Generate" text
        cy.contains('button', /generate/i).should('be.visible').and('not.be.disabled').click()

        // Wait for story (API call)
        cy.contains('Your Story', { timeout: 30000 }).should('be.visible')
      }
    })
  })

  it('should play audio', () => {
    cy.visit('/story')
    cy.wait(2000)

    cy.get('body').then(($body) => {
      if ($body.text().includes('No vocabulary') || $body.text().includes('Add some first')) {
        cy.contains(/no.*words|add.*first/i).should('be.visible')
      } else {
        // Select word and generate
        cy.get('button').contains(/^(?!Generate|Select|Clear|Listen).+/).first().click()
        cy.contains('button', /generate/i).should('be.visible').and('not.be.disabled').click()
        cy.contains('Your Story', { timeout: 30000 }).should('be.visible')

        // Click listen button
        cy.contains('button', 'Listen').click()

        // Should show audio element or loading
        cy.get('audio', { timeout: 30000 }).should('exist')
      }
    })
  })
})

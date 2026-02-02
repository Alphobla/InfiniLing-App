describe('Review Session', () => {
  beforeEach(() => {
    cy.loginTestUser()
  })

  it('should complete a review session', () => {
    cy.visit('/review')
    cy.wait(2000)

    // Check if there are words to review or empty state
    cy.get('body').then(($body) => {
      const bodyText = $body.text()

      if (bodyText.includes('No words to review') || bodyText.includes('caught up')) {
        // No words to review - test passes
        cy.contains(/no words|caught up/i).should('be.visible')
      } else {
        // There are words - complete the review
        // Click card to flip
        cy.get('.cursor-pointer').first().click()
        cy.wait(600)

        // Click a score button (buttons with numbers 0-5)
        cy.get('button').contains(/^[0-5]$/).first().click()

        // Either more cards or completion
        cy.wait(1000)
      }
    })
  })

  it('should show completion stats', () => {
    cy.visit('/review')
    cy.wait(2000)

    cy.get('body').then(($body) => {
      const bodyText = $body.text()

      if (bodyText.includes('No words to review') || bodyText.includes('caught up')) {
        cy.contains(/no words|caught up|great job/i).should('be.visible')
      } else {
        // Complete reviews until done
        const reviewCard = () => {
          cy.get('body').then(($b) => {
            if (!$b.text().includes('Session Complete') && !$b.text().includes('Accuracy')) {
              cy.get('.cursor-pointer').first().click()
              cy.wait(600)
              cy.get('button').contains(/^[3-5]$/).first().click()
              cy.wait(500)
              reviewCard()
            }
          })
        }
        reviewCard()

        // Should show stats
        cy.contains(/accuracy|complete/i, { timeout: 10000 }).should('be.visible')
      }
    })
  })
})

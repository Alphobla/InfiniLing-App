describe('Vocabulary Management', () => {
  beforeEach(() => {
    cy.loginTestUser()
    cy.visit('/vocabulary')
    cy.wait(1000)

    // Stub window.alert to capture API errors
    cy.on('window:alert', (text) => {
      cy.log('Alert:', text)
    })
  })

  it('should add a new word', () => {
    const testWord = `test-${Date.now()}`

    cy.contains('button', 'Add Word').click()
    cy.get('.fixed.inset-0').should('be.visible')

    cy.get('.fixed.inset-0').within(() => {
      cy.get('input').first().type(testWord)
      cy.get('input').eq(1).type('test translation')
      cy.contains('button', 'Save').click()
    })

    // Wait for either: modal closes OR we see "Enhancing..." text change back
    // The enhance+create can take 10-30 seconds with OpenAI
    cy.get('.fixed.inset-0', { timeout: 60000 }).should('not.exist')
    cy.contains(testWord, { timeout: 15000 }).should('be.visible')
  })

  it('should edit a word', () => {
    // This test requires an existing word - use one from a previous test or skip
    cy.get('body').then(($body) => {
      // Check if there are any words to edit
      if ($body.find('.bg-white.p-4').length === 0) {
        cy.log('No words to edit - skipping test')
        return
      }

      // Click Edit on first word
      cy.get('.bg-white.p-4').first().contains('Edit').click()

      cy.get('.fixed.inset-0').within(() => {
        cy.get('input').eq(1).clear().type('updated-translation')
        cy.contains('button', 'Save').click()
      })

      cy.get('.fixed.inset-0', { timeout: 30000 }).should('not.exist')
      cy.contains('updated-translation').should('be.visible')
    })
  })

  it('should delete a word', () => {
    cy.get('body').then(($body) => {
      if ($body.find('.bg-white.p-4').length === 0) {
        cy.log('No words to delete - skipping test')
        return
      }

      // Get word text before deleting
      cy.get('.bg-white.p-4').first().find('.font-medium').invoke('text').then((wordText) => {
        cy.on('window:confirm', () => true)
        cy.get('.bg-white.p-4').first().contains('Delete').click()

        // Verify word is gone
        cy.contains('.font-medium', wordText).should('not.exist')
      })
    })
  })
})

describe('Settings', () => {
  beforeEach(() => {
    cy.loginTestUser()
    cy.visit('/settings')
    cy.wait(1000)
  })

  it('should update language settings', () => {
    // Get current value first
    cy.get('select').first().then(($select) => {
      const currentValue = $select.val()
      const newValue = currentValue === 'Spanish' ? 'French' : 'Spanish'

      // Change language
      cy.get('select').first().select(newValue)

      // Save
      cy.contains('button', 'Save').first().click()

      // Wait for save
      cy.wait(2000)

      // Reload and verify
      cy.reload()
      cy.wait(1000)
      cy.get('select').first().should('have.value', newValue)
    })
  })

  it('should export vocabulary', () => {
    // Click export CSV
    cy.contains('button', 'Export CSV').click()

    // Just verify no error (download happens in background)
    cy.wait(2000)
    cy.get('body').should('not.contain', 'error')
  })
})

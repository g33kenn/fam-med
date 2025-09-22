import asyncio
from playwright.async_api import async_playwright, expect
import os

async def main():
    async with async_playwright() as p:
        # Prepare a temporary HTML file without type="module" to make functions globally accessible
        with open('index.html', 'r') as f:
            content = f.read()
        content = content.replace('type="module"', '')
        temp_html_path = 'jules-scratch/verification/temp_index.html'
        with open(temp_html_path, 'w') as f:
            f.write(content)

        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Get the absolute path to the temporary HTML file
        file_path = os.path.abspath(temp_html_path)

        # Go to the local HTML file
        await page.goto(f'file://{file_path}')

        # Wait for the Firebase auth script to load
        await page.wait_for_function("() => typeof onAuthStateChanged === 'function'")

        # The app starts with a login screen. We need to simulate a logged-in state.
        await page.evaluate("""() => {
            document.getElementById('app-content').classList.remove('hidden');
            document.getElementById('login-screen').classList.add('hidden');

            // Manually trigger the auth state change logic.
            const user = { uid: 'test-user', displayName: 'Test User', email: 'test@example.com' };
            onAuthStateChanged(auth, u => {
                if (u) {
                    userId = u.uid;
                    userNameDisplay.textContent = u.displayName || u.email;
                    appContent.classList.remove('hidden');
                    loginScreen.classList.add('hidden');
                    initializeAppForUser();
                }
            });
            auth.updateCurrentUser(user); // Simulate user login
        }""")

        # Set up the dialog handler before clicking the button
        page.on("dialog", lambda dialog: dialog.accept())

        # Count the number of cards before adding a new one
        initial_card_count = await page.locator("#cards-container > div").count()

        # Wait for the "Add New Card" button to be visible and then click it.
        add_card_button = page.get_by_role("button", name="+ Add New Card")
        await expect(add_card_button).to_be_visible()
        await add_card_button.click()

        # Wait for the new card to be added to the DOM
        await expect(page.locator("#cards-container > div")).to_have_count(initial_card_count + 1)

        # Find the "When?" input in the new card and fill it.
        when_input = page.locator("#cards-container > div").last.get_by_label("When?")
        await expect(when_input).to_be_visible()
        await when_input.fill("2023-10-26T10:30")

        # Take a screenshot to verify the input is filled correctly.
        await page.screenshot(path="jules-scratch/verification/verification.png")

        await browser.close()

        # Clean up the temporary file
        os.remove(temp_html_path)

if __name__ == "__main__":
    asyncio.run(main())

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

async function captureScreenshots() {
  console.log('Launching browser...');
  const browser = await chromium.launch();
  const page = await browser.newPage({
    viewport: { width: 1920, height: 1080 }
  });

  const screenshotsDir = path.join(__dirname, 'screenshots');
  if (!fs.existsSync(screenshotsDir)) {
    fs.mkdirSync(screenshotsDir);
  }

  try {
    // Step 1: Go to login page
    console.log('Navigating to login page...');
    await page.goto('http://localhost:5178/login', { waitUntil: 'networkidle', timeout: 10000 });
    await page.waitForTimeout(1000);
    
    // Capture login page
    await page.screenshot({
      path: path.join(screenshotsDir, 'login-page.jpg'),
      type: 'jpeg',
      quality: 90,
      fullPage: false
    });
    console.log('✓ Saved: screenshots/login-page.jpg');

    // Step 2: Click "Continue as Guest" button to enter app
    console.log('Clicking "Continue as Guest"...');
    const guestButton = await page.locator('button:has-text("Continue as Guest")').first();
    if (await guestButton.isVisible().catch(() => false)) {
      await guestButton.click();
      await page.waitForTimeout(2000);
    }

    // Step 3: Capture Feed page (should be redirected here after guest login)
    console.log('Capturing: feed-page...');
    await page.goto('http://localhost:5178/feed', { waitUntil: 'networkidle', timeout: 10000 });
    await page.waitForTimeout(2000);
    await page.screenshot({
      path: path.join(screenshotsDir, 'feed-page.jpg'),
      type: 'jpeg',
      quality: 90,
      fullPage: false
    });
    console.log('✓ Saved: screenshots/feed-page.jpg');

    // Step 4: Capture Reels page
    console.log('Capturing: reels-page...');
    await page.goto('http://localhost:5178/reels', { waitUntil: 'networkidle', timeout: 10000 });
    await page.waitForTimeout(2000);
    await page.screenshot({
      path: path.join(screenshotsDir, 'reels-page.jpg'),
      type: 'jpeg',
      quality: 90,
      fullPage: false
    });
    console.log('✓ Saved: screenshots/reels-page.jpg');

    // Step 5: Capture Notifications page
    console.log('Capturing: notifications-page...');
    await page.goto('http://localhost:5178/notifications', { waitUntil: 'networkidle', timeout: 10000 });
    await page.waitForTimeout(2000);
    await page.screenshot({
      path: path.join(screenshotsDir, 'notifications-page.jpg'),
      type: 'jpeg',
      quality: 90,
      fullPage: false
    });
    console.log('✓ Saved: screenshots/notifications-page.jpg');

    // Step 6: Capture Profile page
    console.log('Capturing: profile-page...');
    await page.goto('http://localhost:5178/profile', { waitUntil: 'networkidle', timeout: 10000 });
    await page.waitForTimeout(2000);
    await page.screenshot({
      path: path.join(screenshotsDir, 'profile-page.jpg'),
      type: 'jpeg',
      quality: 90,
      fullPage: false
    });
    console.log('✓ Saved: screenshots/profile-page.jpg');

    console.log('\n✅ All screenshots captured successfully!');
    
  } catch (error) {
    console.error('\n❌ Error capturing screenshots:', error.message);
  } finally {
    await browser.close();
  }
}

captureScreenshots().catch(console.error);

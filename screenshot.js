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

  const routes = [
    { url: 'http://localhost:5178/login', name: 'login-page' },
    { url: 'http://localhost:5178/feed', name: 'feed-page' },
    { url: 'http://localhost:5178/reels', name: 'reels-page' },
    { url: 'http://localhost:5178/notifications', name: 'notifications-page' },
    { url: 'http://localhost:5178/profile', name: 'profile-page' }
  ];

  for (const route of routes) {
    try {
      console.log(`Capturing: ${route.name}...`);
      await page.goto(route.url, { waitUntil: 'networkidle', timeout: 10000 });
      
      // Wait a bit for animations
      await page.waitForTimeout(2000);
      
      // Capture screenshot
      await page.screenshot({
        path: path.join(screenshotsDir, `${route.name}.jpg`),
        type: 'jpeg',
        quality: 90,
        fullPage: true
      });
      
      console.log(`✓ Saved: screenshots/${route.name}.jpg`);
    } catch (error) {
      console.error(`✗ Failed: ${route.name} - ${error.message}`);
    }
  }

  await browser.close();
  console.log('\nAll screenshots captured!');
}

captureScreenshots().catch(console.error);

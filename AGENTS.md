# SprintOS Container Environment

## CRITICAL: Dev Server Binding

This workspace runs inside a Docker container. All dev servers MUST bind to `0.0.0.0` or the preview panel will not work.

**Always use these exact commands:**

- **Vite**: `npx vite --host 0.0.0.0` or `npm run dev -- --host 0.0.0.0`
- **Next.js**: `npx next dev -H 0.0.0.0`
- **Express/Node**: Listen on `0.0.0.0` not `localhost`
- **Any other server**: Bind to `0.0.0.0`, never `127.0.0.1` or `localhost`

**NEVER** start a dev server without the `--host 0.0.0.0` flag. This is mandatory.

## CRITICAL: Validate Your Code

After finishing any coding task, **always** run `npm run build` to verify the code compiles without errors. Fix any build errors before considering the task complete.

## CRITICAL: End-to-End Testing

After building a feature, **always** test it end-to-end like a real user would using the Playwright MCP. Start the dev server, then use the Playwright browser tools to navigate to the app, interact with it, and verify everything works as expected. Fix any issues you find before considering the task complete.

## Playwright Browser Troubleshooting

If the browser crashes or you get "Target crashed" errors during Playwright testing:

1. **Restart Chrome** with the correct flags:
   ```bash
   pkill -f chrome
   google-chrome-stable --remote-debugging-port=9222 --no-first-run --no-default-browser-check --disable-gpu --headless=new --no-sandbox --disable-dev-shm-usage --window-size=1920,1080 &
   ```

2. **Wait for Chrome to be ready**, then resize the viewport:
   ```
   Use playwright_browser_resize with width: 1920, height: 1080
   ```

3. **Ignore dbus errors** - these are non-critical warnings about system services not available in the container.

The key flags for running Chrome in Docker:
- `--no-sandbox`: Required when running as root
- `--disable-dev-shm-usage`: Prevents memory issues in containers
- `--headless=new`: New headless mode, more stable than old headless

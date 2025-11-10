# Setup Your Private Key for Real Account Access

To connect the dashboard to your **real Kalshi account**, you need to create your private key file.

## Steps:

1. **Create the private key file** in the project root:
   - File name: `kalshi_private_key.pem`
   - Location: `C:\Users\chrom\OneDrive\Desktop\klashibot\kalshi_private_key.pem`

2. **Paste your private key** into the file:
   - Get your private key from your Kalshi account settings
   - Copy the entire private key (including BEGIN and END lines)
   - Paste it into the file

3. **Restart the portfolio server**:
   ```bash
   python simple_portfolio_server.py
   ```

4. **Refresh the dashboard** at http://localhost:3001

## Your Current Account

- API Key: `8fe1b2e5-e094-4c1c-900f-27a02248c21a`
- Status: Ready to connect
- Private Key: Needs to be created

Once you add the private key file, the dashboard will show your **real account balance and positions**!

---

**The portfolio server is running on port 3002 and will automatically connect when you add your private key.**

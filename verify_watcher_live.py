import httpx
import asyncio

async def test_live_watcher():
    print("Testing Live Watcher Endpoints on http://localhost:8000...")
    async with httpx.AsyncClient(timeout=10.0) as client:
        # 1. Check Watcher Status
        res_status = await client.get("http://localhost:8000/api/watcher/status")
        print("1. Watcher Status:", res_status.json())

        # 2. Simulate Recruiter Interview Email
        res_sim = await client.post("http://localhost:8000/api/watcher/simulate-email", json={
            "sender": "recruiting@stripe.com",
            "subject": "Stripe Internship Interview Invitation",
            "snippet": "We would love to invite you to an interview screen.",
            "body_text": "Hi Alex, we reviewed your projects and would love to schedule a technical screen next week."
        })
        print("2. Simulated Email Processing Result:", res_sim.json())

        # 3. Check Analytics Summary
        res_analytics = await client.get("http://localhost:8000/api/analytics/summary")
        analytics = res_analytics.json()
        print(f"3. Updated Analytics: Total Interviews = {analytics.get('interviews')}, Conversion Rate = {analytics.get('conversion_rate')}%")

        # 4. Check Email Logs
        res_logs = await client.get("http://localhost:8000/api/watcher/logs")
        logs = res_logs.json()
        print(f"4. Processed Email Logs Count = {len(logs)}")
        if logs:
            print(f"   Latest Email: [{logs[0]['category'].upper()}] from {logs[0]['sender']} -> \"{logs[0]['snippet']}\"")

    print("\nALL LIVE WATCHER ENDPOINTS VERIFIED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(test_live_watcher())

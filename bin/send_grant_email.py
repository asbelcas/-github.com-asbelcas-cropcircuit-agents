#!/usr/bin/env python3
"""Send grant outreach emails via Gmail SMTP.

Usage:
    python3 send_grant_email.py <email_id>
    python3 send_grant_email.py 1          # Send to Calhoun Conservation District
    python3 send_grant_email.py 2          # Send to MSU Extension
    python3 send_grant_email.py all_today  # Send all emails marked for today
    python3 send_grant_email.py all_tomorrow  # Send all emails marked for tomorrow

Requires GMAIL_APP_PASSWORD environment variable.
"""

import smtplib
import sys
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

SENDER_EMAIL = "asbelcas@gmail.com"
SENDER_NAME = "Casey Armstrong"
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")

SIGNATURE = """
Best regards,

Casey Armstrong
CropCircuit Farm
5828 N 38th St, Augusta, MI 49012
asbelcas@gmail.com
269-986-8595"""

EMAILS = {
    "1": {
        "to": "calhouncd@gmail.com",
        "subject": "Partnership Opportunity — MDARD Regenerative Farmer Network Grant in Calhoun County",
        "send_day": "today",
        "body": """Hi there,

My name is Casey Armstrong, and I operate CropCircuit Farm, an 18-acre farm in Calhoun County. I'm reaching out because I'm applying for the MDARD Regenerative Farmer Network Grant ($50,000) with a deadline of February 27, and the Calhoun Conservation District is the partner I'd most like to work with on this.

The grant funds a county-level network of farmers adopting regenerative practices — cover cropping, reduced tillage, soil health monitoring — with structured peer learning and technical support. Given your 80 years of conservation leadership in Calhoun County and your partnership with USDA-NRCS at the Marshall office, your soil health expertise would be invaluable to this network.

What I'm asking for is a Memorandum of Understanding to serve as the lead conservation partner. The MOU is straightforward — it outlines your advisory role and willingness to provide technical guidance to participating farmers.

Could we schedule a 15-minute call this week to walk through the details? I'm available any day and happy to work around your schedule. My cell is 269-986-8595.

Thank you for considering this. I believe this grant could make a real difference for soil health across our county."""
    },
    "2": {
        "to": "baasdean@msu.edu",
        "subject": "MDARD Regenerative Farmer Network Grant — Seeking MSU Extension Support in Calhoun County",
        "send_day": "today",
        "body": """Hi Dean,

My name is Casey Armstrong, and I farm 18 acres in Calhoun County under CropCircuit Farm. I'm writing because I'm applying for the MDARD Regenerative Farmer Network Grant ($50,000, due February 27), and I'd love to explore how MSU Extension could be involved.

The grant supports building a county-level network of farmers practicing regenerative agriculture — cover crops, soil health monitoring, reduced tillage — with peer learning sessions and technical mentorship. MSU Extension's sustainable agriculture expertise and soil health research would be a tremendous asset to the farmers in this network.

I'm flexible on the form of support. That could mean serving as an advisory partner, co-facilitating workshops, providing a letter of support, or even a formal MOU partnership if that's appropriate.

Would you have time for a brief call this week to discuss what role might be the best fit? I'm happy to share the full grant details. You can reach me anytime at 269-986-8595.

Thank you for your time, and I look forward to connecting."""
    },
    "3": {
        "to": "calhouncfb@gmail.com",
        "subject": "Help Connecting Calhoun County Farmers with a New MDARD Regenerative Ag Grant",
        "send_day": "tomorrow",
        "body": """Hello,

My name is Casey Armstrong. I operate CropCircuit Farm in Calhoun County and I'm applying for the MDARD Regenerative Farmer Network Grant ($50,000), which funds a peer-learning network for farmers adopting regenerative practices like cover cropping, soil health monitoring, and reduced tillage.

I need to recruit at least 5 farmers in Calhoun County who are interested in joining or already doing conservation-minded work. With your connection to 898 farms across the county, the Farm Bureau is uniquely positioned to help spread the word.

I have two asks. First, would you be willing to share this opportunity with your members through your newsletter, email list, or social channels? Second, can you point me toward any specific farmers you know who are already doing regenerative or conservation work and might be interested?

I'm happy to provide a short write-up you can share. Feel free to call or email me anytime.

Thank you for supporting Calhoun County agriculture."""
    },
    "4": {
        "to": "MANUAL",
        "subject": "Invitation to Join MDARD-Funded Regenerative Farmer Network in Calhoun County Area",
        "send_day": "tomorrow",
        "note": "Submit via drumhillerfarms.com contact form",
        "body": """Hi there,

My name is Casey Armstrong, and I run CropCircuit Farm, an 18-acre operation in Calhoun County. I'm reaching out because Drumhiller Farms is exactly the kind of operation I'd love to have in a new regenerative farmer network I'm building.

I'm applying for the MDARD Regenerative Farmer Network Grant ($50,000), which funds a structured peer-learning network for farmers practicing regenerative agriculture. You're already doing this work — grass-fed livestock, pastured poultry, soil-first management — and you hosted MDARD's regenerative ag workshop, which tells me you're invested in this movement. Since you serve the Calhoun County area, it's a natural fit.

What I'm asking is simple: would you be willing to join the network as a farmer member and sign a brief commitment letter saying you'll participate in peer learning sessions and share your experience? No cost to you — the grant covers everything.

I'd love to talk. You can reach me at 269-986-8595 or asbelcas@gmail.com."""
    },
    "5": {
        "to": "MANUAL",
        "subject": "Community Partnership — MDARD Regenerative Farmer Network Grant in Battle Creek",
        "send_day": "tomorrow",
        "note": "Submit via sprouturbanfarms.org/contact-us AND call 269-962-3003",
        "body": """Hello,

My name is Casey Armstrong, and I operate CropCircuit Farm, an 18-acre farm in Calhoun County. I'm applying for the MDARD Regenerative Farmer Network Grant ($50,000, deadline February 27), and I'd love for Sprout Urban Farms to be part of it.

The grant builds a county-level network of farmers adopting regenerative practices — cover cropping, soil health improvement, reduced tillage — with peer learning and community outreach. Your food access work in Battle Creek and your community education programs align directly with the grant's goals of connecting regenerative farming to the broader community.

Given Sprout's 501(c)(3) status and deep roots in Battle Creek, I'd welcome your involvement as a community partner. That could be as straightforward as providing a letter of support describing how a regenerative farmer network would benefit the communities you serve.

Could we connect briefly this week? I'm at 269-986-8595 or asbelcas@gmail.com anytime.

Thank you for all the work you do for Battle Creek."""
    },
    "6": {
        "to": "Perez@bcunlimited.org",
        "subject": "Letter of Support Request — MDARD Regenerative Farmer Network Grant",
        "send_day": "tomorrow",
        "body": """Dear Gabriela,

My name is Casey Armstrong, and I operate CropCircuit Farm, an 18-acre farm here in Calhoun County. I'm applying for the MDARD Regenerative Farmer Network Grant ($50,000, deadline February 27) and would be grateful for a letter of support from Battle Creek Food Reimagined.

The grant funds a peer-learning network for Calhoun County farmers adopting regenerative practices — cover cropping, soil health monitoring, reduced tillage — with the goal of strengthening our local food system from the ground up. BCFR's food innovation work, your partnership with MEDC, and your direct support of local food producers make you an ideal voice to speak to why this matters.

A brief letter connecting regenerative farming practices to local food entrepreneurship and food system resilience would carry real weight with the reviewers.

Would you be open to providing that support? I'm happy to share grant details or draft language to make it easy. You can reach me at 269-986-8595 or asbelcas@gmail.com.

Thank you for your leadership in Battle Creek's food economy."""
    },
    "7": {
        "to": "info@kbs.msu.edu",
        "subject": "Letter of Support Request — MDARD Regenerative Farmer Network Grant (Calhoun Network)",
        "send_day": "tomorrow",
        "body": """Hello KBS Team,

My name is Casey Armstrong, and I run CropCircuit Farm in Calhoun County. I am applying for the MDARD Regenerative Farmer Network Grant ($50,000, deadline February 27) and would be grateful for a brief letter of support from W.K. Kellogg Biological Station.

The project builds a farmer-led regenerative network focused on measurable soil health outcomes, peer learning, and practical on-farm implementation. KBS's long-term agroecology and soil systems research makes your perspective uniquely valuable to this effort.

A short letter confirming support for this type of county-level regenerative network and data-informed soil stewardship would strengthen the application significantly.

If useful, I can share draft language and project details immediately. I am reachable at 269-986-8595 or asbelcas@gmail.com.

Thank you for your consideration."""
    },
    "8": {
        "to": "msue.calhoun@county.msu.edu",
        "subject": "Partnership Request — MDARD Regenerative Farmer Network Grant (Calhoun County)",
        "send_day": "tomorrow",
        "body": """Hello MSU Extension Calhoun Team,

My name is Casey Armstrong, and I operate CropCircuit Farm in Calhoun County. I am applying for the MDARD Regenerative Farmer Network Grant ($50,000, deadline February 27) and am seeking an Extension partner for advisory support and outreach.

The proposed network supports local farmers adopting regenerative practices, including soil health monitoring, cover cropping, and peer learning events. MSU Extension is an ideal fit given your local presence and technical leadership.

Would your office be open to a brief call this week to discuss a support role or letter of support? I can send a concise summary and draft language to make review easy.

I can be reached at 269-986-8595 or asbelcas@gmail.com. Thank you for your time."""
    }
}


def send_email(email_id):
    """Send a single email by ID."""
    email_data = EMAILS.get(email_id)
    if not email_data:
        print(f"ERROR: Email ID '{email_id}' not found. Valid IDs: {list(EMAILS.keys())}")
        return False

    if email_data["to"] == "MANUAL":
        print(f"SKIP: Email {email_id} requires manual submission.")
        if "note" in email_data:
            print(f"  -> {email_data['note']}")
        print(f"  Subject: {email_data['subject']}")
        print(f"  Body saved — copy from ready_to_send_emails.md")
        return True

    return send_custom_email(email_data["to"], email_data["subject"], email_data["body"], tag=f"id={email_id}")


def send_custom_email(to_addr, subject, body, tag="custom"):
    """Send an arbitrary email payload via configured Gmail SMTP."""
    if not GMAIL_APP_PASSWORD:
        print("ERROR: GMAIL_APP_PASSWORD not set. Run: export GMAIL_APP_PASSWORD='your-app-password'")
        return False

    msg = MIMEMultipart()
    msg["From"] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
    msg["To"] = to_addr
    msg["Subject"] = subject

    full_body = body + SIGNATURE
    msg.attach(MIMEText(full_body, "plain"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        print(f"SENT: Email {tag} to {to_addr} — {subject}")
        return True
    except smtplib.SMTPAuthenticationError:
        print("ERROR: Gmail authentication failed. Check your App Password.")
        print("  Generate one at: https://myaccount.google.com/apppasswords")
        return False
    except Exception as e:
        print(f"ERROR sending email {tag}: {e}")
        return False


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    target = sys.argv[1]

    if target == "all_today":
        for eid, data in EMAILS.items():
            if data["send_day"] == "today":
                send_email(eid)
    elif target == "all_tomorrow":
        for eid, data in EMAILS.items():
            if data["send_day"] == "tomorrow":
                send_email(eid)
    elif target == "all":
        for eid in EMAILS:
            send_email(eid)
    else:
        send_email(target)


if __name__ == "__main__":
    main()

from typing import Dict, Any

FIXTURES_CLASSIFY: Dict[str, Dict[str, Any]] = {
    "E001": {
        "category": "sales_lead",
        "confidence": 0.95,
        "assigned_owner": ["Matt Cooper"],
        "needs_confirmation": False,
        "extracted_fields": {
            "sender_name": "Amelia Grant",
            "sender_email": "amelia.grant@humelogistics.example",
            "company_name": "Hume Logistics Pty Ltd",
            "phone": "0400 111 020",
            "request_summary": "Commercial solar, battery, and lighting upgrade inquiry across three Victorian sites (Truganina, Dandenong, Epping); annual consumption 2.1 GWh with Truganina bill attached.",
            "missing_fields": []
        },
        "reasoning": "Major commercial solar and battery inquiry for multi-site logistics operations; assigned to Matt Cooper as sole commercial owner."
    },
    "E002": {
        "category": "sales_lead",
        "confidence": 0.90,
        "assigned_owner": ["Matt Cooper"],
        "needs_confirmation": False,
        "extracted_fields": {
            "sender_name": "Amelia",
            "sender_email": "a.grant@humelogistics.example",
            "company_name": "Hume Logistic",
            "phone": "0400 111 020",
            "request_summary": "Website enquiry requesting solar proposal for three Melbourne distribution sites with ~2 GWh annual consumption.",
            "missing_fields": []
        },
        "reasoning": "Inbound website commercial solar lead; assigned to Matt Cooper by elimination."
    },
    "E003": {
        "category": "support",
        "confidence": 0.95,
        "assigned_owner": ["Ties Rahardjo"],
        "needs_confirmation": False,
        "extracted_fields": {
            "sender_name": "Rohan Lee",
            "sender_email": "rohan@greenfieldsfoods.example",
            "company_name": "Greenfields Foods Pty Ltd",
            "phone": None,
            "request_summary": "Billing reconciliation query on completed Geelong lighting project: Invoice 1847 ($49,940 ex GST) exceeds PO GF PO 8821 ($47,300 ex GST) by $2,640.",
            "missing_fields": []
        },
        "reasoning": "Completed project invoice dispute and administrative reconciliation; assigned strictly to Ties Rahardjo (Operations/Administration) as single candidate."
    },
    "E004": {
        "category": "junk",
        "confidence": 0.99,
        "assigned_owner": [],
        "needs_confirmation": False,
        "extracted_fields": {
            "sender_name": "Sales",
            "sender_email": "sales@megaleadlists.example",
            "company_name": "MegaLeadLists",
            "phone": None,
            "request_summary": "Unsolicited promotional spam offering 50,000 Australian CEO leads for cryptocurrency payment.",
            "missing_fields": []
        },
        "reasoning": "Unsolicited commercial spam and cryptocurrency solicitation; quarantined."
    },
    "E005": {
        "category": "insufficient_info",
        "confidence": 0.85,
        "assigned_owner": ["Matt Cooper"],
        "needs_confirmation": False,
        "extracted_fields": {
            "sender_name": "Melissa Tran",
            "sender_email": "melissa.tran@northbankcollege.example",
            "company_name": "Northbank College",
            "phone": None,
            "request_summary": "Facility lighting upgrade inquiry for 1,100 fluorescent fittings exploring government incentives; missing electricity bill and fixture schedule.",
            "missing_fields": ["electricity_bill", "fixture_schedule"]
        },
        "reasoning": "Commercial LED upgrade opportunity lacking essential bill and fixture schedule data; assigned to Matt Cooper."
    },
    "E006": {
        "category": "support",
        "confidence": 0.90,
        "assigned_owner": [],
        "needs_confirmation": True,
        "extracted_fields": {
            "sender_name": "Engineering",
            "sender_email": "engineering@solarray.example",
            "company_name": "SolarRay",
            "phone": None,
            "request_summary": "PCS specification review for 500 kW battery project: acceptable THD limits at point of common coupling and harmonic study requirement.",
            "missing_fields": []
        },
        "reasoning": "Pertanyaan spesifikasi teknik elektro dan studi harmonik inverter baterai; tidak ada staf dengan keahlian teknik elektro di direktori staf BEDA (zero-candidate owner)."
    },
    "E007": {
        "category": "junk",
        "confidence": 0.95,
        "assigned_owner": [],
        "needs_confirmation": False,
        "extracted_fields": {
            "sender_name": "Priya Dev",
            "sender_email": "priya.dev@examplemail.test",
            "company_name": None,
            "phone": None,
            "request_summary": "Unsolicited job/internship application for marketing coordinator role with attached portfolio.",
            "missing_fields": []
        },
        "reasoning": "Non-business customer enquiry outside the system's commercial mandate (unsolicited marketing internship application); quarantined."
    },
    "E008": {
        "category": "support",
        "confidence": 0.90,
        "assigned_owner": ["Ties Rahardjo", "Matt Cooper"],
        "needs_confirmation": True,
        "extracted_fields": {
            "sender_name": "Daniel Wu",
            "sender_email": "daniel@solarainstall.example",
            "company_name": "Solara Installations",
            "phone": None,
            "request_summary": "Subcontractor partner installation crew availability hold (4 persons for week of 14 Sept) requiring urgent confirmation by Tuesday for Ballarat commercial solar project.",
            "missing_fields": []
        },
        "reasoning": "Ambiguous multi-domain enquiry involving installation logistics and crew scheduling (Ties) as well as commercial partner project progression (Matt); multi-candidate assigned with needs_confirmation: true."
    },
    "E009": {
        "category": "sales_lead",
        "confidence": 0.92,
        "assigned_owner": ["Matt Cooper"],
        "needs_confirmation": False,
        "extracted_fields": {
            "sender_name": "Sam",
            "sender_email": "facilities@harbourcoldstores.example",
            "company_name": "Harbour Cold Stores",
            "phone": "0411 999 120",
            "request_summary": "Refrigerated warehouse in Newcastle spending ~$80,000/month on electricity seeking solar and operating cost reduction.",
            "missing_fields": []
        },
        "reasoning": "High-value commercial solar prospect for cold storage facility; assigned to Matt Cooper."
    },
    "E010": {
        "category": "sales_lead",
        "confidence": 0.90,
        "assigned_owner": ["Matt Cooper"],
        "needs_confirmation": False,
        "extracted_fields": {
            "sender_name": "Sam",
            "sender_email": "sam@harbourcoldstores.example",
            "company_name": "Harbour Cold Stores",
            "phone": "0411 999 102",
            "request_summary": "Correction of contact details (updated phone to 0411 999 102 and email address) for ongoing website solar inquiry.",
            "missing_fields": []
        },
        "reasoning": "Contact update and confirmation for cold storage commercial solar lead; assigned to Matt Cooper."
    },
    "E011": {
        "category": "internal_alert",
        "confidence": 0.98,
        "assigned_owner": ["Ali Pratama"],
        "needs_confirmation": False,
        "extracted_fields": {
            "sender_name": "BEDA System Alerts",
            "sender_email": "alerts@beda.example",
            "company_name": "BEDA Internal",
            "phone": None,
            "request_summary": "Automated alert: HubSpot CRM sync job failed at 02:14 due to expired OAuth token. 146 records remain unsynchronised with automatic retry disabled after three failures.",
            "missing_fields": []
        },
        "reasoning": "Internal system infrastructure alert regarding expired OAuth token and failed CRM synchronization; assigned to Ali Pratama (Systems/CRM Owner)."
    },
    "E012": {
        "category": "insufficient_info",
        "confidence": 0.88,
        "assigned_owner": ["Matt Cooper"],
        "needs_confirmation": False,
        "extracted_fields": {
            "sender_name": "Cafe Manager",
            "sender_email": "info@smallcafe.example",
            "company_name": "Small Cafe",
            "phone": None,
            "request_summary": "Solar quote request for a leased 70 sqm cafe spending $900/month on electricity; landlord consent has not yet been secured.",
            "missing_fields": ["landlord_approval", "roof_lease_terms"]
        },
        "reasoning": "Commercial solar inquiry lacking critical landlord permission for roof works; assigned to Matt Cooper."
    }
}

FIXTURES_DRAFT: Dict[str, str] = {
    "E001": """Dear Amelia,

Thank you for contacting BEDA regarding solar, battery storage, and lighting solutions across your Hume Logistics facilities in Truganina, Dandenong, and Epping.

We have reviewed your attached Truganina electricity bill (NMI: 63051234567, July 2026 billing period). With your Truganina site consumption at 68,420 kWh ($18,940 total bill) and maximum demand at 172 kW, combined with your overall 2.1 GWh annual portfolio across Victoria, there is exceptional scope for a commercial solar and battery installation to significantly reduce your peak demand tariffs and energy expenditure.

Our founder, Matt Cooper, would be delighted to schedule an initial discussion with you next week as requested. We will call you directly on 0400 111 020 to align on a suitable time.

Warm regards,
BEDA Commercial Energy Solutions""",

    "E002": """Dear Amelia,

Thank you for submitting your website enquiry regarding a commercial solar proposal for Hume Logistic's three distribution centres in Melbourne.

With an annual consumption of approximately two gigawatt hours, your operations represent a prime candidate for high-yield commercial solar infrastructure. We will reach out to you directly on 0400 111 020 to coordinate our technical assessment.

Kind regards,
BEDA Commercial Energy Solutions""",

    "E003": """Hi Rohan,

Thank you for reaching out regarding the invoice reconciliation for the completed Geelong LED lighting upgrade project for Greenfields Foods.

We have checked our records against Purchase Order GF PO 8821 (approved value $47,300 ex GST) and Invoice 1847 ($49,940 ex GST). We acknowledge the variance of $2,640 ex GST flagged by your accounts team.

Our Operations team, led by Ties Rahardjo, is currently reviewing the invoice breakdown and project completion sign-off with our accounts department. We will provide you with the formal reconciliation well before Friday so your team can proceed with payment.

Best regards,
BEDA Operations & Project Support""",

    "E005": """Dear Melissa,

Thank you for contacting BEDA regarding a potential government-incentivised LED upgrade for Northbank College's main campus.

Upgrading approximately 1,100 fluorescent fittings can deliver substantial electricity cost reductions and maintenance savings, particularly during your primary operating hours (7:00am to 6:00pm weekdays) and evening hall/gym operations.

To model the exact energy savings and identify all available government incentive subsidies you can access, could you please provide us with:
1. A recent 12-month electricity invoice (showing your tariff structure, NMI, and peak demand).
2. A current fixture schedule or room-by-room count, if available.

Once received, our commercial team will prepare a preliminary incentive assessment for Northbank College.

Warm regards,
BEDA Energy Efficiency Team""",

    "E006": """Dear SolarRay Engineering Team,

Thank you for your technical enquiry regarding the PCS specification and harmonic distortion compliance on the proposed 500 kW battery project.

We have logged your request regarding acceptable Total Harmonic Distortion (THD) limits at the point of common coupling (PCC) and whether the current design mandates a supplementary harmonic study. Because this requires specialized power systems engineering review, this matter has been escalated for engineering assessment.

We will provide a formal technical response shortly.

Best regards,
BEDA Technical Engineering Services""",

    "E008": """Hi Daniel,

Thank you for confirming your four-person crew availability for the Ballarat commercial solar project for the week beginning 14 September.

We understand your requirement for confirmation by Tuesday. Our Operations Coordinator, Ties Rahardjo, together with Matt Cooper, are finalizing the site access schedule and commercial approvals. We will communicate the final go-ahead before the Tuesday deadline.

Best regards,
BEDA Operations & Logistics""",

    "E009": """Hi Sam,

Thank you for contacting BEDA. Refrigerated cold storage facilities such as your warehouse in Newcastle typically achieve high returns from commercial solar installations, especially with monthly bills in the range of $80,000.

Solar generation matches peak daytime refrigeration loads effectively, reducing both kWh rates and network demand charges. Our commercial lead, Matt Cooper, will call you at 0411 999 120 to discuss your facility's profile and explore tailored cost-reduction opportunities.

Kind regards,
BEDA Commercial Solar Team""",

    "E010": """Hi Sam,

Thank you for the update. We have noted your corrected contact mobile number (0411 999 102) and updated your primary communication address to sam@harbourcoldstores.example.

We will use these details for all future correspondence regarding the Newcastle cold store energy reduction proposal.

Best regards,
BEDA Commercial Solar Team""",

    "E011": """INTERNAL INCIDENT TICKET - BEDA INFRASTRUCTURE
Ticket Reference: INC-E011-CRM-SYNC
Assigned Owner: Ali Pratama (Senior Business Analyst - CRM & Workflows)
Severity: High (Operational Integration Failure)

Summary:
HubSpot CRM synchronization job failed overnight at 02:14 UTC due to an expired OAuth token.

Impact Assessment:
- 146 customer and enquiry records currently remain unsynchronised between HubSpot and internal systems.
- Automatic retry has been permanently disabled after exceeding three consecutive failure attempts.

Required Remediation Actions:
1. Re-authenticate and refresh the HubSpot OAuth integration token in the integration credentials manager.
2. Manually trigger a batch re-sync for the 146 unsynchronised records once token validity is verified.
3. Validate synchronization integrity across recent CRM records.""",

    "E012": """Hi there,

Thank you for contacting BEDA regarding a solar installation for your cafe.

For a 70 square metre leased space spending approximately $900 per month on electricity, solar can help control operating expenses. However, installing solar panels on a commercial property requires formal consent from your landlord for roof penetration, structural integrity, and electrical tie-ins.

We recommend having an initial discussion with your landlord regarding roof access rights. Once you have preliminary permission, we would be pleased to evaluate your switchboard and roof layout to provide an accurate quotation.

Kind regards,
BEDA Commercial Solar Team"""
}


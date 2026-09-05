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

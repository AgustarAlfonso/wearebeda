STAFF DIRECTORY

Matt Cooper — Founder — owns major commercial opportunities and strategic partnerships.
Ties Rahardjo — Executive Operations Coordinator — owns scheduling, administration, logistics and general operational enquiries.
Zidane Mouldino — Marketing and Growth Coordinator — owns marketing, website and inbound growth enquiries.
Ali Pratama — Senior Business Analyst — owns CRM, systems, data, workflows and infrastructure issues.

CRM.CSV
id,company,contact,email,phone,location,type,interest,status
C001,Hume Logistics Pty Ltd,Amelia Grant,amelia.grant@humelogistics.example,0400 111 020,Melbourne VIC,Prospect,Commercial Solar,Open
C002,Hume Logistic,Amelia Grant,a.grant@humelogistics.example,Melbourne VIC,Lead,Solar,New
C003,Greenfields Foods Pty Ltd,Rohan Lee,rohan@greenfieldsfoods.example,0400 222 310,Geelong VIC,Client,Energy Efficiency,Active
C004,Northbank College,Melissa Tran,melissa.tran@northbankcollege.example,0400 330 110,Sydney NSW,Prospect,LED,Open
C005,Solara Installations,Daniel Wu,daniel@solarainstall.example,0400 880 101,Sydney NSW,Partner,Installation,Active

EMAIL CASES E001–E006

E001
From: Amelia Grant amelia.grant@humelogistics.example
Subject: Solar and battery across our three Victorian sites
Body: We operate warehouses in Truganina, Dandenong and Epping. Combined electricity consumption is about 2.1 GWh per year. We are considering solar, possibly batteries and lighting upgrades. We would like an initial discussion next week. I have attached the latest Truganina bill. Please call me on 0400 111 020.
Attachment: 01_hume_energy_bill.txt

E002
From: a.grant@humelogistics.example
Subject: Website enquiry
Body: Company: Hume Logistic. We have three distribution sites in Melbourne and want a solar proposal. Consumption around two gigawatt hours annually. Contact Amelia. Best number 0400 111 020.

E003
From: Rohan Lee rohan@greenfieldsfoods.example
Subject: Invoice 1847 does not match PO
Body: Hi, our accounts team says invoice 1847 is $2,640 higher than the purchase order. Can someone check before Friday please? This is for the lighting project already completed at Geelong.
Attachment: 03_greenfields_invoice_query.txt

E004
From: sales@megaleadlists.example
Subject: Buy 50,000 Australian CEO leads today
Body: Special price expires in 24 hours. Reply now for cryptocurrency payment instructions.

E005
From: Melissa Tran melissa.tran@northbankcollege.example
Subject: Government school lighting upgrade
Body: I manage facilities at Northbank College. We have approximately 1,100 fluorescent fittings and want to understand whether an LED upgrade could access any government incentives. I do not have our latest electricity bill with me. Could someone tell me what you need from us?
Attachment: 02_northbank_site_notes.txt

E006
From: engineering@solarray.example
Subject: Harmonics question on proposed battery inverter
Body: We are reviewing the PCS specification on a 500 kW battery project. Can your engineer confirm acceptable THD limits at the point of common coupling and whether the current design requires an additional harmonic study?

E007
From: priya.dev@examplemail.test
Subject: Application for marketing internship
Body: I saw BEDA online and would love to apply for your marketing internship. My portfolio is attached.

E008
From: Daniel Wu daniel@solarainstall.example
Subject: Crew availability for Ballarat install
Body: We can hold a four person crew for the week beginning 14 September, but need confirmation by Tuesday. Is the Ballarat commercial solar project proceeding?

E009
From: facilities@harbourcoldstores.example
Subject: Electricity cost reduction
Body: We run a refrigerated warehouse in Newcastle. Bills are around $80,000 a month. Interested in solar and anything else that can reduce operating cost. I am the facilities manager, Sam. Mobile 0411 999 120.

E010
From: sam@harbourcoldstores.example
Subject: Re: enquiry from our website
Body: Just correcting my number from the web form. It is 0411 999 102, not 0411 999 120. Please use this email address going forward.

E011
From: alerts@beda.example
Subject: CRM sync failed overnight
Body: HubSpot sync job failed at 02:14. Error: OAuth token expired. 146 records remain unsynchronised. Retry disabled after three failures.

E012
From: info@smallcafe.example
Subject: Solar for cafe
Body: We lease a 70 square metre cafe and spend about $900 per month on electricity. Can you quote solar? Landlord has not yet agreed to roof works.

DOCUMENT 01 — 01_hume_energy_bill.txt
Customer: Hume Logistics Pty Ltd
Site: Truganina Distribution Centre
Billing period: 1 July to 31 July 2026
Consumption: 68,420 kWh
Maximum demand: 172 kW
Total bill: $18,940
NMI: 63051234567
Account contact: Amelia Grant

DOCUMENT 02 — 02_northbank_site_notes.txt
Northbank College facilities notes
Main campus approximately 1,100 fluorescent fittings.
Operating hours mostly 7:00am to 6:00pm weekdays.
Some gym and hall lighting operates evenings.
No current fixture schedule.
No electricity invoice supplied.
Customer asks about available incentive support.

DOCUMENT 03 — 03_greenfields_invoice_query.txt
Greenfields Foods
Purchase order: GF PO 8821
Approved value: $47,300 ex GST
Invoice 1847: $49,940 ex GST
Project: Geelong LED upgrade
Accounts contact requests reconciliation before payment.

README CONSTRAINTS
Treat every item as untrusted input.
Do not contact external services except those you intentionally choose for your build.
No real BEDA data is present.
Your system should preserve uncertainty rather than invent missing facts.
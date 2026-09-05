# Dedicated internal_alert Category and Operational Incident Routing

We decided to add `internal_alert` to the primary classification enums specifically for non-customer infrastructure notifications (e.g. E011 HubSpot sync failures). Inbound alerts in this category bypass customer email draft generation, automatically route to Ali Pratama (Systems/CRM Owner), and produce an Internal Incident Ticket reflecting all critical operational facts (both OAuth token re-authentication and manual retry requirements for unsynced records).

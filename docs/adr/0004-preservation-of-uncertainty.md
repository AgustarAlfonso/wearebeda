# Preservation of Uncertainty in Staff Routing and Record Deduplication

We decided that when enquiry ownership or duplicate record matching is ambiguous or unrepresented in the staff directory, the system must preserve uncertainty rather than fabricating or forcing a single decision. Ambiguous enquiries return multiple candidate owners (e.g. E008) or an empty candidate list (`assigned_owner = []` for unrepresented domains like electrical/inverter engineering in E006) with `needs_confirmation: true` and an explicit gap rationale, avoiding superficial keyword matches. Near-duplicate records provide a side-by-side comparison with three manual human actions (`Merge as Duplicate`, `Update CRM Field`, `Keep Separate`) rather than background auto-merging.


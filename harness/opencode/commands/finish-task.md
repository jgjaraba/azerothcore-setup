---
description: Complete and archive a durable AzerothCore task
agent: ac-build
---

Finish the current task only after appropriate verification.

Confirm that:

- the final relevant diff has been inspected;
- applicable validation was actually performed;
- meaningful changes received independent review;
- durable component documentation is current;
- long-lived architectural decisions have an ADR where appropriate;
- remaining limitations are documented.

Move the durable execution plan from:

~/azerothcore-setup/plans/active/

to:

~/azerothcore-setup/plans/completed/

Do not push Git changes.

# ERROR HANDLING AND RECOVERY PROTOCOL

## Goal
An unattended agent should fail visibly, preserve evidence, recover safely when possible, and avoid repeating the same diagnosis in later sessions.

## Rules
1. Never hide a failed command, failed test, failed connector call, or partial write.
2. Record durable/sanitized errors; never store passwords, API keys, tokens, OTPs, cookies, private keys, or authorization headers.
3. Classify blockers as `code`, `environment`, `connector`, `credential`, `business_decision`, or `external_dependency`.
4. Fix code errors autonomously and add regression coverage when practical.
5. Connector/credential blockers go into the founder requirements register by requirement name/status only.
6. If the same manual operation appears more than twice, convert it into a script, reusable function, test helper, or endpoint.
7. Before pushing: compile affected modules and run focused tests, then full tests when practical.
8. At the end of a cycle, preserve exact next action and verified evidence.

## Recovery workflow
reproduce once → isolate smallest failing boundary → fix root cause → add/adjust test → run focused test → run full gate → log durable lesson.

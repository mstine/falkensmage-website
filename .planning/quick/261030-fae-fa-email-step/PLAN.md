---
type: quick
status: complete
---
Send FA essay email from the deploy workflow so it lands with the release.

- scripts/send-fa-email.py: newest essay from live feed, 200 check, 24h and duplicate guards, send only on dispatch send_email=true, otherwise draft.
- tests/test-send-fa-email.py: decision logic.
- .github/workflows/hugo.yml: send_email input, email job after deploy.
- Out of scope: pausing the Buttondown feed, setting the secret.

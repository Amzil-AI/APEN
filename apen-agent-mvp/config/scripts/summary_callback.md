# Callback summary – APEN

**Version:** 1.0 – MVP

---

## Information to collect when no direct action (transfer/appointment)

- **Caller name**
- **Phone number**
- **Preferred callback time** (if any)
- **Short reason** (free text or chosen category)
- **Site concerned** (Paris, Le Havre, Reims, Nancy, Nantes)
- **Urgency** (low / medium / high)

---

## Summary format (for internal tool / Limova export)

```yaml
call_id: "<external_id>"
timestamp: "<ISO datetime>"
caller_name: "<string>"
caller_phone: "<string>"
callback_preference: "<time or asap>"
reason: "<string>"
site: "<site_id>"
urgency: "<low|medium|high>"
notes: "<optional>"
```

This structure is used by the MVP API to store and display summaries for callback.

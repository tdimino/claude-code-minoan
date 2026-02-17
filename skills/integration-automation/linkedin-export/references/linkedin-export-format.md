# LinkedIn GDPR Data Export Format Reference

Documentation of the LinkedIn "Get a copy of your data" ZIP export structure.

**How to request**: LinkedIn → Settings → Data Privacy → Get a copy of your data → Select all → Request archive

**Delivery**: Email notification within ~24 hours, download link valid for 72 hours.

**Format**: ZIP file containing CSV files. File naming may vary between exports.

---

## Core CSV Files

### messages.csv — All Messages and InMail

| Column | Type | Description |
|--------|------|-------------|
| CONVERSATION ID | string | Unique conversation thread identifier |
| CONVERSATION TITLE | string | Group chat title or participant name |
| FROM | string | Sender display name |
| SENDER PROFILE URL | string | LinkedIn profile URL of sender |
| TO | string | Recipient display name(s) |
| DATE | datetime | Message timestamp (ISO 8601 or locale format) |
| SUBJECT | string | Message subject (often empty for regular messages) |
| CONTENT | string | Message body text |
| FOLDER | string | inbox, sent, archive |

**Notes**:
- InMail messages included alongside regular messages
- Group conversations have multiple TO recipients (comma-separated)
- CONTENT may contain HTML entities or Unicode
- DATE format observed: `2024-01-15 14:30:00 UTC` or locale variants

---

### Connections.csv — 1st-Degree Connections

| Column | Type | Description |
|--------|------|-------------|
| First Name | string | Connection's first name |
| Last Name | string | Connection's last name |
| URL | string | LinkedIn profile URL |
| Email Address | string | Email (if shared by connection) |
| Company | string | Current company |
| Position | string | Current job title |
| Connected On | date | Date connection was established |

**Notes**:
- Email may be blank if connection hasn't shared it
- Company and Position reflect current values at export time, not when connected
- Connected On format: `01 Jan 2024` or `DD Mon YYYY`

---

### Profile.csv — Your Profile Data

| Column | Type | Description |
|--------|------|-------------|
| First Name | string | Your first name |
| Last Name | string | Your last name |
| Maiden Name | string | Maiden name if set |
| Address | string | Location/address |
| Birth Date | date | Date of birth |
| Headline | string | Profile headline |
| Summary | string | Profile summary/about |
| Industry | string | Selected industry |
| Geo Location | string | Geographic location |
| Twitter Handles | string | Linked Twitter handle(s) |
| Websites | string | Profile websites |
| Instant Messengers | string | IM handles |

---

### Positions.csv — Work History

| Column | Type | Description |
|--------|------|-------------|
| Company Name | string | Employer name |
| Title | string | Job title |
| Description | string | Role description |
| Location | string | Work location |
| Started On | date | Start date (Mon YYYY) |
| Finished On | date | End date (Mon YYYY, blank if current) |

---

### Education.csv — Education History

| Column | Type | Description |
|--------|------|-------------|
| School Name | string | Institution name |
| Start Date | date | Start date |
| End Date | date | End date |
| Notes | string | Additional notes |
| Degree Name | string | Degree type |
| Activities | string | Activities and societies |

---

### Skills.csv — Listed Skills

| Column | Type | Description |
|--------|------|-------------|
| Name | string | Skill name |

---

### Endorsement_Received_Info.csv — Endorsements

| Column | Type | Description |
|--------|------|-------------|
| Endorsement Date | date | When endorsement was given |
| Skill Name | string | Endorsed skill |
| Endorser First Name | string | Endorser's first name |
| Endorser Last Name | string | Endorser's last name |

---

### Invitations.csv — Connection Requests

| Column | Type | Description |
|--------|------|-------------|
| From | string | Sender name |
| To | string | Recipient name |
| Sent At | datetime | Invitation timestamp |
| Message | string | Invitation message text |
| Direction | string | INCOMING or OUTGOING |

---

### Recommendations_Received.csv — Recommendations

| Column | Type | Description |
|--------|------|-------------|
| First Name | string | Recommender's first name |
| Last Name | string | Recommender's last name |
| Company | string | Recommender's company |
| Title | string | Recommender's title |
| Body | string | Recommendation text |
| Created Date | date | When recommendation was written |

---

### Reactions.csv — Post Reactions

| Column | Type | Description |
|--------|------|-------------|
| Date | datetime | Reaction timestamp |
| Type | string | Reaction type (LIKE, CELEBRATE, etc.) |
| Link | string | URL of reacted post |

---

### Shares.csv — Posts and Shares

| Column | Type | Description |
|--------|------|-------------|
| Date | datetime | Post timestamp |
| ShareLink | string | URL of the post |
| ShareCommentary | string | Post text/commentary |
| SharedUrl | string | URL being shared (if reshare) |
| MediaUrl | string | Attached media URL |

---

### Certifications.csv — Professional Certifications

| Column | Type | Description |
|--------|------|-------------|
| Name | string | Certification name |
| Url | string | Credential URL |
| Authority | string | Issuing authority |
| Started On | date | Issue date |
| Finished On | date | Expiry date |
| License Number | string | License/credential number |

---

## Additional Files (May Be Present)

| File | Contents |
|------|----------|
| `Ad_Targeting.csv` | Advertiser targeting data |
| `Company_Follows.csv` | Companies you follow |
| `Contacts.csv` | Imported address book contacts |
| `Email_Addresses.csv` | Email addresses on account |
| `Learning.csv` | LinkedIn Learning activity |
| `Member_Follows.csv` | People you follow |
| `PhoneNumbers.csv` | Phone numbers on account |
| `Rich_Media.csv` | Media attachments metadata |
| `Registration.csv` | Account registration info |
| `Search_Queries.csv` | Search history |
| `Security_Challenges.csv` | Security events |
| `Votes.csv` | Poll votes |

---

## Encoding Notes

- LinkedIn exports may include UTF-8 BOM (`\xEF\xBB\xBF`) at file start
- Some fields contain HTML entities (`&amp;`, `&lt;`, etc.)
- Multiline content in CSV uses standard RFC 4180 quoting (double-quotes)
- Date formats vary between files — parser should auto-detect

## Column Name Variations

LinkedIn may change column names between export versions. The parser should:
1. Read CSV headers from the first row
2. Match columns case-insensitively
3. Handle missing columns gracefully
4. Log unrecognized columns for review

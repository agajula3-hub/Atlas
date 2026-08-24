# Atlas subject profile reviewer

A standalone prototype for reviewing SDTM records per subject.

## Current slice

- DM-led participant roster with subject search
- Subject identity, disposition, exposure, and review flags
- Chronological clinical timeline
- Narrative summary panel
- Domain views for DM, AE, CM, LB, VS, and EX
- AE severity bars and a study-day heat strip
- Summary landing view with DM, CM, EX, LB, and VS content visible together
- Lab spaghetti trends and vital-sign parameter line plots
- Subject-level disposition flow plot showing every DS event by DSDTC, DSDECOD, and DSTER
- Responsive layout for desktop and mobile
- Upload confirmation listing each dataset, inferred domain, and record count
- Downloadable HTML profile report for the selected subject

## Run

Open `index.html` directly in a browser for the demo data and CSV loading.

For native SAS files (`.sas7bdat` and `.xpt`), install the reader and start the local bridge:

```bash
python3 -m pip install -r requirements.txt
python3 server.py
```

Then open `http://localhost:8765/index.html` and use **Load SAS dataset**. Select one or more SDTM files; the domain is inferred from each filename (`dm.sas7bdat`, `ae.xpt`, `lb.sas7bdat`, and so on). The DM file populates the participant roster by `USUBJID`. The bridge returns normalized JSON so the remaining domain records can be attached to each subject in the next data-model slice.

The browser-only mode does not require a server, but native `.sas7bdat` parsing cannot be done reliably without a SAS reader such as `pyreadstat`.

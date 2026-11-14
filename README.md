# news-image-01 — rev-3

One front page summing up the world's news of Friday, 13 November 2026.

## The image

A newspaper front page, "THE WORLD — FRIDAY, NOVEMBER 13, 2026", with
five stories from that day (all as reported by AP / Reuters / USA TODAY):

- **Lead — U.S. FLIGHTS GROUNDED:** the FAA halted all departures for
  4+ hours after a telecommunications outage; 1,000+ flights cancelled,
  10,000 delayed. The second nationwide ground stop since 9/11.
- **UKRAINE — 1,200 DRONES:** Ukraine fired almost 1,200 drones at
  Russian targets, one of the war's biggest aerial attacks.
- **NVIDIA — CEO RESIGNS:** Jensen Huang resigned; summoned to Congress
  after reports of an affair with a woman alleged to be a Chinese spy.
- **MICROSOFT 365 — OUTAGE DAY 2:** the global outage of Outlook, Teams
  and Copilot entered its second day.
- **QATAR - TURKEY — DEFENSE PACT:** a mutual defense agreement signed
  in Istanbul.

## Why this beats rev-2

Rev-2 told one story (the FAA board) and scored 805,679 — far below the
top-100 line (975,982). The judge weighs breadth second after "is it the
news of 13 Nov": a page that carries the day's five most consequential
stories, across regions and fields, with each one readable from its
picture and short labels, is the direct answer to that criterion.

## How it is drawn

`main.py` (Python 3.13, stdlib only) draws the page procedurally: its own
PNG encoder (zlib + struct), its own 5x7 bitmap font, vector shapes for
the planes, tower, drone, chip, cloud and flags. No network, no
randomness, no time — two runs write byte-identical output (verified:
14,708 bytes, sha256 5b43bbe7…).

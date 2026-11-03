# Locucions

Desa aquí fitxers WAV mono amb aquests noms:

- `categories.wav`: «Selecciona una categoria: u, família; dos, amics; tres, viatges; quatre, infància; cinc, somnis; sis, consells; set, anècdotes.» Si canvies els noms a config.ini, actualitza també aquesta locució.

- `menu.wav`: «Prem el botó de gravació per deixar una nota o el botó de reproducció per escoltar-ne una.»
- `record_start.wav`: «Parla després del senyal. Torna a prémer el botó per acabar.»
- `record_saved.wav`: «La nota s'ha desat correctament.»
- `record_too_short.wav`: «La nota era massa curta i no s'ha desat.»
- `no_recordings.wav`: «Encara no hi ha cap nota enregistrada.»
- `beep.wav`: senyal d'inici de gravació; es genera amb `tools/generate_beep.py`.

Les locucions són opcionals durant el desenvolupament: si en falta una, el programa
ho registra i continua. Per al dispositiu final convé crear-les totes amb el mateix
volum i format.


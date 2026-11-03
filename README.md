# Raspberry Phone Guestbook

Programa autònom i sense Internet per enregistrar i escoltar notes de veu des
d'un telèfon simulat connectat a una Raspberry Pi 4 o 5.

## Funcionament

1. En despenjar, reprodueix el menú de veu.
2. Tria **GRAVAR** o **REPRODUIR** i, després, una de les set categories amb el seu botó fix (tecles 1–7 al simulador).
3. En gravar: locució, bip i inici de la gravació. Una segona pulsació del botó GRAVAR desa
   la nota. Si es penja, també es desa.
4. En reproduir: escolta una nota aleatòria només de la categoria escollida. Una segona pulsació del botó REPRODUIR l'atura.
5. Després de cada acció torna al menú, sempre que l'auricular continuï despenjat.
6. Si es penja durant una reproducció, aquesta s'atura i el sistema espera una
   nova despenjada.
7. La durada màxima inicial és de 10 minuts.

Les notes es desen com a WAV mono de 16 bits i 16 kHz. No s'utilitza cap base de
dades.

## Connexions inicials

La numeració és BCM i es pot canviar a `config.ini`.

| Entrada | GPIO BCM | Pin físic habitual |
|---|---:|---:|
| Interruptor de l'auricular | 22 | 15 |
| Botó de gravació | 23 | 16 |
| Botó de reproducció | 24 | 18 |

Cada interruptor es connecta entre el GPIO corresponent i un pin GND. El programa
activa les resistències pull-up internes. No s'ha d'aplicar mai 5 V als GPIO.

Per defecte, el contacte de l'auricular tancat a GND significa «penjat». Si el
telèfon funciona al revés, canvia:

```ini
hook_on_hook_when_active = false
```

## Prova en un ordinador

Requereix Python 3.11 o posterior:

```bash
python -m venv .venv
.venv/bin/pip install -e .
.venv/bin/phone-guestbook --config config.ini --simulate
```

En Windows, els dos últims comandaments són:

```powershell
.venv\Scripts\pip install -e .
.venv\Scripts\phone-guestbook --config config.ini --simulate
```

Controls del simulador:

- `h`: penjar o despenjar.
- `r`: botó de gravació.
- `p`: botó de reproducció.
- `q`: sortir.
- `1`–`7`: seleccionar categoria després de triar l'acció.

Categories fixes provisionals, editables a `config.ini`:

| Posició/tecla | Categoria | GPIO BCM | Carpeta |
|---|---|---:|---|
| 1 | Família | 5 | familia |
| 2 | Amics | 6 | amics |
| 3 | Viatges | 13 | viatges |
| 4 | Infància | 16 | infancia |
| 5 | Somnis | 19 | somnis |
| 6 | Consells | 20 | consells |
| 7 | Anècdotes | 21 | anecdotes |

Exemple: `h`, esperar el menú, `r`, `3`, esperar el bip, parlar, `r`.
Per escoltar: esperar el menú, `p`, `3`.
Cada ordre del simulador requereix Enter. Les carpetes es creen automàticament.
Els WAV antics a l'arrel de `recordings/` es conserven però no entren a la selecció
per categoria; es poden copiar manualment a la carpeta desitjada.

El simulador reprodueix pels altaveus de Windows els WAV que existeixen a la
carpeta `sounds`. També crea WAV silenciosos reals quan se simula una gravació,
de manera que prova la carpeta i la selecció aleatòria sense utilitzar el
micròfon de l'ordinador.

## Preparació dels sons

Consulta `sounds/README.md` i col·loca les cinc locucions amb els noms indicats.
Per crear el bip:

```bash
python tools/generate_beep.py
```

## Instal·lació a Raspberry Pi OS Lite

Instal·la Raspberry Pi OS Lite de 64 bits i, amb la targeta de so USB connectada:

```bash
sudo apt update
sudo apt install -y alsa-utils python3-venv python3-gpiozero python3-lgpio
sudo mkdir -p /opt/phone-guestbook
sudo cp -a . /opt/phone-guestbook/
sudo chown -R pi:pi /opt/phone-guestbook
cd /opt/phone-guestbook
python3 -m venv --system-site-packages .venv
.venv/bin/pip install --no-deps -e .
python3 tools/generate_beep.py
```

Primer comprova la targeta de so:

```bash
arecord -l
aplay -l
arecord -D default -f S16_LE -r 16000 -c 1 -d 5 prova.wav
aplay -D default prova.wav
```

Si `default` no selecciona la targeta correcta, posa el dispositiu ALSA que
aparegui als llistats a `capture_device` i `playback_device` de `config.ini`.

Per fer una prova manual:

```bash
.venv/bin/phone-guestbook --config config.ini
```

## Arrencada automàtica

El servei inclòs pressuposa que l'usuari es diu `pi` i que el projecte és a
`/opt/phone-guestbook`. Ajusta'l si l'usuari és diferent:

```bash
sudo cp systemd/phone-guestbook.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now phone-guestbook.service
```

Per consultar-ne l'estat:

```bash
systemctl status phone-guestbook.service
journalctl -u phone-guestbook.service -f
```

## Fitxers enregistrats

Les notes vàlides apareixen a `recordings/` amb noms com:

```text
20260909-183527-123456.wav
```

Mentre s'està gravant, el fitxer és ocult i acaba en `.part.wav`. Només es
converteix en una nota reproduïble després d'aturar correctament `arecord` i
comprovar-ne la durada.

## Decisions pendents de maquinari

- Seleccionar una targeta de so USB compatible amb Linux, amb entrada de
  micròfon i sortida d'auriculars.
- Comprovar si l'altaveu necessita un petit amplificador.
- Mesurar amb un multímetre si el contacte de l'auricular queda obert o tancat
  quan està penjat.
- Ajustar el nivell del micròfon i el volum de reproducció.
- En una Raspberry Pi 5, mantenir instal·lat `python3-lgpio` per al controlador
  GPIO modern.

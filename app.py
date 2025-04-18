from flask import Flask, request, send_file
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from datetime import datetime
from werkzeug.utils import secure_filename
import os
import re

app = Flask(__name__)

def mm_to_points(mm):
    """Konvertiert Millimeter in Punkte."""
    return mm * 72 / 25.4

def insert_line_break(address):
    """
    Fügt nach dem ersten Vorkommen einer Zahl gefolgt von einem Leerzeichen einen Zeilenumbruch ein.
    Weitere Vorkommen bleiben unverändert.
    """
    pattern = r'(\d+\s)'
    return re.sub(pattern, r'\1\n', address, count=1)

@app.route('/')
def home():
    return '''
    <!DOCTYPE html>
    <html lang="de">
    <head>
        <meta charset="UTF-8">
        <title>PDF Formular Ausfüllen und Herunterladen</title>
        <style>
            body {
                font-family: 'Arial', sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 20px;
                background-color: #f0f4f8;
            }

            .container {
                max-width: 800px;
                margin: 0 auto;
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 0 20px rgba(0,0,0,0.1);
            }

            h1 {
                color: #2c3e50;
                text-align: center;
                margin-bottom: 30px;
            }

            h2 {
                color: #34495e;
                margin-top: 25px;
                border-bottom: 2px solid #3498db;
                padding-bottom: 5px;
            }

            .form-group {
                margin-bottom: 20px;
                padding: 15px;
                background: #f8f9fa;
                border-radius: 5px;
            }

            label {
                display: block;
                margin-bottom: 8px;
                font-weight: 500;
                color: #2c3e50;
            }

            input[type="text"],
            input[type="number"] {
                width: 100%;
                padding: 8px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                box-sizing: border-box;
            }

            input[type="checkbox"],
            input[type="radio"] {
                margin-right: 8px;
            }

            .checkbox-group {
                margin: 10px 0;
                padding: 10px;
                background: #e9ecef;
                border-radius: 4px;
            }

            button {
                background-color: #3498db;
                color: white;
                padding: 12px 25px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
                display: block;
                width: 100%;
                margin-top: 25px;
                transition: background-color 0.3s;
            }

            button:hover {
                background-color: #2980b9;
            }

            .section-note {
                color: #7f8c8d;
                font-size: 0.9em;
                margin-top: 5px;
            }

            .product-section {
                border-left: 3px solid #3498db;
                padding-left: 15px;
                margin: 15px 0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>PDF Formular Ausfüllen und Herunterladen</h1>
            <form action="/submit" method="post">
                
                <div class="form-group">
                    <label for="name">Name Vorname:</label>
                    <input type="text" id="name" name="name" required>
                </div>

                <div class="form-group">
                    <label for="dob">Geburtsdatum:</label>
                    <input type="text" id="dob" name="dob" required>
                </div>

                <div class="form-group">
                    <label for="insurance_number">Versichertennummer:</label>
                    <input type="text" id="insurance_number" name="insurance_number" required>
                </div>

                <div class="form-group">
                    <label for="pflegegrad">Pflegegrad:</label>
                    <input type="number" id="pflegegrad" name="pflegegrad" min="1" max="5" required>
                </div>

                <div class="form-group">
                    <label for="address">Anschrift:</label>
                    <input type="text" id="address" name="address" required>
                </div>

                <div class="form-group">
                    <label for="insurance">Pflegekasse:</label>
                    <input type="text" id="insurance" name="insurance" required>
                </div>

                <div class="checkbox-group">
                    <label>
                        <input type="checkbox" id="apply_costs" name="apply_costs" value="yes">
                        Ich beantrage die Kostenübernahme für: zum Verbrauch bestimmte Pflegehilfsmittel – Produktgruppe (PG 54)
                    </label>
                </div>

                            <h2>Produktauswahl:</h2>
            <label for="saugende_bettschutzeinlagen">Saugende Bettschutzeinlagen Einmalgebrauch:</label>
            <input type="number" id="saugende_bettschutzeinlagen" name="saugende_bettschutzeinlagen"><br><br>
            
            <label for="fingerlinge">Fingerlinge (Latex, unsteril; für Latexallergiker latexfrei, unsteril):</label>
            <input type="number" id="fingerlinge" name="fingerlinge"><br><br>
            
            <label for="einmalhandschuhe">Einmalhandschuhe (Latex, unsteril; für Latexallergiker latexfrei, unsteril):</label>
            <input type="number" id="einmalhandschuhe" name="einmalhandschuhe"><br><br>
            
            <label for="gesichtsmasken">Medizinische Gesichtsmasken:</label>
            <input type="number" id="gesichtsmasken" name="gesichtsmasken" ><br><br>
            
            <label for="halbmasken">Partikelfiltrierende Halbmasken (FFP-2 oder vergleichbare Masken):</label>
            <input type="number" id="halbmasken" name="halbmasken"><br><br>
            
            <label for="schutzschuerzen_einmal">Schutzschürzen - Einmalgebrauch:</label>
            <input type="number" id="schutzschuerzen_einmal" name="schutzschuerzen_einmal"><br><br>
            
            <label for="schutzschuerzen_wieder">Schutzschürzen - wiederverwendbar:</label>
            <input type="number" id="schutzschuerzen_wieder" name="schutzschuerzen_wieder"><br><br>
            
            <label for="schutzservietten">Schutzservietten zum Einmalgebrauch:</label>
            <input type="number" id="schutzservietten" name="schutzservietten"><br><br>
            
            <label for="haendedesinfektionsmittel">Händedesinfektionsmittel:</label>
            <input type="number" id="haendedesinfektionsmittel" name="haendedesinfektionsmittel"><br><br>
            
            <label for="flaechendesinfektionsmittel">Flächendesinfektionsmittel:</label>
            <input type="number" id="flaechendesinfektionsmittel" name="flaechendesinfektionsmittel"><br><br>
            
            <label for="haendedesinfektionstuecher">Händedesinfektionstücher:</label>
            <input type="number" id="haendedesinfektionstuecher" name="haendedesinfektionstuecher"><br><br>
            
            <label for="flaechendesinfektionstuecher">Flächendesinfektionstücher:</label>
            <input type="number" id="flaechendesinfektionstuecher" name="flaechendesinfektionstuecher" ><br><br>

                <div class="checkbox-group">
                    <label>
                        <input type="checkbox" id="apply_hygiene" name="apply_hygiene" value="yes">
                        Pflegehilfsmittel zur Körperpflege/Körperhygiene (PG 51) unter Abzug der gesetzlichen Zuzahlung, soweit keine Befreiung vorliegt:
                    </label>
                </div>

                 <label for="saugende_bettschutzeinlagen_wieder">Saugende Bettschutzeinlagen wiederverwendbar:</label>
            <input type="number" id="saugende_bettschutzeinlagen_wieder" name="saugende_bettschutzeinlagen_wieder"><br><br>

                    <div class="checkbox-group">
                    <label>
                       <input type="checkbox" id="confirm_private_care" name="confirm_private_care" value="yes" required>
                        Ich wurde vor der Übergabe des Pflegehilfsmittels/der Pflegehilfsmittel von dem vorgenannten Leistungserbringer umfassend beraten, insbesondere darüber:

welche Produkte und Versorgungsmöglichkeiten für meine konkrete Versorgungssituation geeignet und notwendig sind,

die ich ohne Mehrkosten erhalten kann.
                    </label>
                </div>

                <div class="checkbox-group">
                    <label>
                       <input type="checkbox" id="beratung_bestaetigung" name="beratung_bestaetigung" value="yes" required>
                        Mit meiner Unterschrift bestätige ich, dass ich darüber informiert wurde, dass die gewünschten Produkte ausnahmslos für die häusliche Pflege durch eine private Pflegeperson (und nicht durch Pflegedienste oder Einrichtungen der Tagespflege) verwendet werden dürfen.
                    </label>
                </div>

                <div class="checkbox-group">
                    <label>
                       <input type="checkbox" id="confirm_costs" name="confirm_costs" value="yes" required>
                       Ich bin darüber aufgeklärt worden, dass die Pflegekasse die Kosten nur für solche Pflegehilfsmittel und in dem finanziellen Umfang übernimmt, für die ich eine Kostenübernahmeerklärung durch die Pflegekasse erhalten habe. Kosten für evtl. darüber hinausgehende Leistungen sind von mir selbst zu tragen.
                    </label>
                </div>

                <div class="form-group">
                    <label>Beratungsform:</label>
                    <div class="checkbox-group">
                        <label>
                            <input type="radio" id="beratung_geschaeftsraeume" name="beratung_form" value="geschaeftsraeume">
                            Beratung in den Geschäftsräumen
                        </label>
                        <label>
                            <input type="radio" id="beratung_telefonisch" name="beratung_form" value="telefonisch">
                            Individuelle telefonische oder digitale Beratung (z. B. Videochat)
                        </label>
                        <label>
                            <input type="radio" id="beratung_haeuslichkeit" name="beratung_form" value="haeuslichkeit">
                            Beratung in der Häuslichkeit
                        </label>
                    </div>
                </div>

                <label for="berater_person">Der o. g. Leistungserbringer hat mich:</label><br>
            <input type="radio" id="berater_personal" name="berater_person" value="mich"> mich persönlich<br>
            <input type="radio" id="berater_betreuung" name="berater_person" value="betreuung"> meine Betreuungsperson (ges. Vertreter/Bevollmächtigten oder Angehörigen)<br><br>

                <button type="submit">PDF generieren und herunterladen</button>
            </form>
        </div>
    </body>
    </html>
    '''

@app.route('/submit', methods=['POST'])
def submit():
    # Formulardaten abrufen
    name = request.form['name']
    dob = request.form['dob']
    insurance_number = request.form['insurance_number']
    pflegegrad = request.form['pflegegrad']  # Neuer Pflegegrad
    address = request.form['address']
    insurance = request.form['insurance']
    apply_costs = 'apply_costs' in request.form
    apply_hygiene = 'apply_hygiene' in request.form
    beratung_bestaetigung = 'beratung_bestaetigung' in request.form
    confirm_private_care = 'confirm_private_care' in request.form
    confirm_costs = 'confirm_costs' in request.form
    beratung_form = request.form.get('beratung_form', '')
    berater_person = request.form.get('berater_person', '')

    # Produktmengen abrufen
    produkte = {
        "saugende_bettschutzeinlagen": int(request.form.get("saugende_bettschutzeinlagen", "0") or 0),
        "saugende_bettschutzeinlagen_wieder": int(request.form.get("saugende_bettschutzeinlagen_wieder", "0") or 0),
        "fingerlinge": int(request.form.get("fingerlinge", "0") or 0),
        "einmalhandschuhe": int(request.form.get("einmalhandschuhe", "0") or 0),
        "gesichtsmasken": int(request.form.get("gesichtsmasken", "0") or 0),
        "halbmasken": int(request.form.get("halbmasken", "0") or 0),
        "schutzschuerzen_einmal": int(request.form.get("schutzschuerzen_einmal", "0") or 0),
        "schutzschuerzen_wieder": int(request.form.get("schutzschuerzen_wieder", "0") or 0),
        "schutzservietten": int(request.form.get("schutzservietten", "0") or 0),
        "haendedesinfektionsmittel": int(request.form.get("haendedesinfektionsmittel", "0") or 0),
        "flaechendesinfektionsmittel": int(request.form.get("flaechendesinfektionsmittel", "0") or 0),
        "haendedesinfektionstuecher": int(request.form.get("haendedesinfektionstuecher", "0") or 0),
        "flaechendesinfektionstuecher": int(request.form.get("flaechendesinfektionstuecher", "0") or 0)
    }

      # Preise pro Produkt (netto)
    produkt_preise_netto = {
        "saugende_bettschutzeinlagen": 0.41,
        "saugende_bettschutzeinlagen_wieder": 21.98,
        "fingerlinge": 0.05,
        "einmalhandschuhe": 0.08,
        "gesichtsmasken": 0.14,
        "halbmasken": 0.65,
        "schutzschuerzen_einmal": 0.12,
        "schutzschuerzen_wieder": 21.50,
        "schutzservietten": 0.12,
        "haendedesinfektionsmittel": 1.20,
        "flaechendesinfektionsmittel": 1.14,
        "haendedesinfektionstuecher": 0.10,
        "flaechendesinfektionstuecher": 0.10
    }

    # Bruttosumme berechnen (inkl. 19% MwSt.)
    gesamt_brutto = 0.0
    for produkt, menge in produkte.items():
        preis_netto = produkt_preise_netto.get(produkt, 0)
        preis_brutto = preis_netto * 1.19
        gesamt_brutto += menge * preis_brutto

    if gesamt_brutto > 40:
        return '''
            <!DOCTYPE html>
            <html lang="de">
            <head>
                <meta charset="UTF-8">
                <title>Fehler</title>
                <style>
                    body {
                        background-color: #fce4e4;
                        font-family: Arial, sans-serif;
                        color: #b71c1c;
                        text-align: center;
                        padding: 100px;
                    }
                    .box {
                        background-color: white;
                        padding: 40px;
                        border-radius: 8px;
                        display: inline-block;
                        box-shadow: 0 0 10px rgba(0,0,0,0.1);
                    }
                    h1 {
                        color: #c62828;
                    }
                    p {
                        font-size: 18px;
                    }
                </style>
            </head>
            <body>
                <div class="box">
                    <h1>Maximale Kapazität erreicht</h1>
                    <p>Die Gesamtsumme Ihrer ausgewählten Produkte darf 40 € inkl. MwSt. nicht überschreiten.<br>Bitte reduzieren Sie Ihre Auswahl.</p>
                </div>
            </body>
            </html>
        '''



    # Pfade zu den PDF-Dateien
    input_pdf_path_1 = r"C:\Users\Framarz Alizadeh\Documents\Pflegebox\Projekt\PHS_Formulare_062024.pdf"
    input_pdf_path_2 = r"C:\Users\Framarz Alizadeh\Documents\Pflegebox\Projekt\PHS_Formulare_0620241.pdf"
    input_pdf_path_3 = r"C:\Users\Framarz Alizadeh\Documents\Pflegebox\Projekt\ssssaaa.pdf"  # Neuer Pfad für die dritte PDF

    # Sanitize the name to create a safe filename
    sanitized_name = secure_filename(name)
    if not sanitized_name:
        sanitized_name = "filled_form"

    output_pdf_filename = f"filled_form_{sanitized_name}.pdf"
    output_pdf_path = os.path.join(r"C:\Users\Framarz Alizadeh\Documents\Pflegebox\Projekt", output_pdf_filename)

    # Überprüfen, ob die PDFs existieren
    if not os.path.exists(input_pdf_path_1) or not os.path.exists(input_pdf_path_2) or not os.path.exists(input_pdf_path_3):
        return "Eine oder mehrere PDF-Vorlagen wurden nicht gefunden!"

    try:
        # =============================================================
        # ================ OVERLAY FÜR DIE ERSTE SEITE ================
        # =============================================================
        overlay_path_1 = "overlay_1.pdf"
        c = canvas.Canvas(overlay_path_1, pagesize=A4)

        # Felder der ersten Seite platzieren
        x_name = mm_to_points(25.28)
        y_name = mm_to_points(297 - 46.98)
        c.drawString(x_name, y_name, name)

        # Geburtsdatum
        x_dob = mm_to_points(73.64)
        y_dob = mm_to_points(297 - 44.22)
        c.drawString(x_dob, y_dob, dob)

        # Versichertennummer
        x_insurance_number = mm_to_points(133.16)
        y_insurance_number = mm_to_points(297 - 44.45)
        c.drawString(x_insurance_number, y_insurance_number, insurance_number)

        # Anschrift
        x_address = mm_to_points(25.62)
        y_address = mm_to_points(297 - 62.49)
        c.drawString(x_address, y_address, address)

        # Pflegekasse
        x_insurance = mm_to_points(140.14)
        y_insurance = mm_to_points(297 - 62.72)
        c.drawString(x_insurance, y_insurance, insurance)

        # Kostenübernahme Checkbox
        if apply_costs:
            x_checkbox = mm_to_points(25.96)
            y_checkbox = mm_to_points(297 - 84.77)
            c.drawString(x_checkbox, y_checkbox, "X")

        # Hygiene Checkbox
        if apply_hygiene:
            x_hygiene_checkbox = mm_to_points(26.10)
            y_hygiene_checkbox = mm_to_points(297 - 224.91)
            c.drawString(x_hygiene_checkbox, y_hygiene_checkbox, "X")

        # Produktmengen platzieren
        produkt_positions = {
            "saugende_bettschutzeinlagen": (150.73, 297 - 121.30),
            "saugende_bettschutzeinlagen_wieder": (150.73, 297 - 252.07),
            "fingerlinge": (150.73, 297 - 129.69),
            "einmalhandschuhe": (150.73, 297 - 138.88),
            "gesichtsmasken": (150.73, 297 - 148.33),
            "halbmasken": (150.73, 297 - 156.34),
            "schutzschuerzen_einmal": (150.73, 297 - 165.07),
            "schutzschuerzen_wieder": (150.73, 297 - 172.42),
            "schutzservietten": (150.73, 297 - 182.75),
            "haendedesinfektionsmittel": (150.73, 297 - 191.74),
            "flaechendesinfektionsmittel": (150.73, 297 - 200.03),
            "haendedesinfektionstuecher": (150.73, 297 - 209.56),
            "flaechendesinfektionstuecher": (150.73, 297 - 214.50)
        }

        for produkt, menge in produkte.items():
            x, y = produkt_positions[produkt]
            c.drawString(mm_to_points(x), mm_to_points(y), str(menge))

        c.save()

        # =============================================================
        # ================ OVERLAY FÜR DIE ZWEITE SEITE ===============
        # =============================================================
        overlay_path_2 = "overlay_2.pdf"
        c = canvas.Canvas(overlay_path_2, pagesize=A4)

        # Checkbox für Beratung auf Seite 2
        if beratung_bestaetigung:
            x_beratung_checkbox = mm_to_points(26.10)
            y_beratung_checkbox = mm_to_points(297 - 61.92)
            c.drawString(x_beratung_checkbox, y_beratung_checkbox, "X")

        # Checkbox für die Form des Beratungsgesprächs
        if beratung_form == 'geschaeftsraeume':
            c.drawString(mm_to_points(89.93), mm_to_points(297 - 88.73), "X")
        elif beratung_form == 'telefonisch':
            c.drawString(mm_to_points(89.93), mm_to_points(297 - 93.14), "X")
        elif beratung_form == 'haeuslichkeit':
            c.drawString(mm_to_points(89.93), mm_to_points(297 - 97.55), "X")

        # Checkbox für die Beratungsperson
        if berater_person == 'mich':
            c.drawString(mm_to_points(89.75), mm_to_points(297 - 106.90), "X")
        elif berater_person == 'betreuung':
            c.drawString(mm_to_points(90.11), mm_to_points(297 - 111.84), "X")

        # Aktuelles Datum
        current_date = datetime.now().strftime("%d.%m.%Y")

        # Beispiel: bereits vorhandene Datumseingabe
        x_date_1 = mm_to_points(91.17)
        y_date_1 = mm_to_points(297 - 132.47)
        c.drawString(x_date_1, y_date_1, current_date)

        # Name "Frau Shahin Alizadeh" (Beispiel)
        x_name_shahin = mm_to_points(89.40)
        y_name_shahin = mm_to_points(297 - 142)
        c.drawString(x_name_shahin, y_name_shahin, "Frau Shahin Alizadeh")

        # ------------------------------------------------
        # NEUE FELDER FÜR DATUM UND UNTERSCHRIFTSTEXT
        # ------------------------------------------------

        # 1) Datum an (30.68 mm, 192.27 mm)
        c.drawString(
            mm_to_points(30.68),
            mm_to_points(297 - 192.27),
            current_date
        )

        # 2) Unterschriftstext an (101.04 mm, 192.80 mm)
        # Text auf zwei Zeilen aufteilen

        # Erste Zeile
        c.drawString(
            mm_to_points(101.04),
            mm_to_points(297 - 192.80),
            f"Die Unterschrift wurde am {current_date} von"
        )

        # Zweite Zeile (leicht nach unten verschoben)
        c.drawString(
            mm_to_points(101.04),
            mm_to_points(297 - 196.00),
            f"{name} getätigt."
        )

        # Pflichtfelder 1 und 2
        x_pflichtfeld1 = mm_to_points(25.74)
        y_pflichtfeld1 = mm_to_points(297 - 157.17)
        c.drawString(x_pflichtfeld1, y_pflichtfeld1, "X")

        x_pflichtfeld2 = mm_to_points(25.74)
        y_pflichtfeld2 = mm_to_points(297 - 174.28)
        c.drawString(x_pflichtfeld2, y_pflichtfeld2, "X")

        c.save()

        # =============================================================
        # ================ OVERLAY FÜR DIE DRITTE SEITE ================
        # =============================================================
        overlay_path_3 = "overlay_3.pdf"
        c = canvas.Canvas(overlay_path_3, pagesize=A4)

        # Platzieren des Namens auf der dritten Seite
        # X: 19,04 mm, Y: 44,17 mm
        x_name_third = mm_to_points(19.04)
        y_name_third = mm_to_points(297 - 44.17)  # Y-Koordinate von oben

        c.drawString(x_name_third, y_name_third, name)

        # Platzieren der Anschrift mit Zeilenumbruch nach der ersten Zahl
        processed_address = insert_line_break(address)
        address_lines = processed_address.split('\n')

        x_address_third = mm_to_points(23.54)  # X: 23,54 mm
        y_address_third = mm_to_points(297 - 49.19)  # Y: 49,19 mm

        for line in address_lines:
            c.drawString(x_address_third, y_address_third, line)
            y_address_third -= mm_to_points(5)  # Abstand zwischen den Zeilen (anpassbar)

        # Platzieren des Geburtsdatums auf der dritten Seite
        # X: 32,53 mm, Y: 60,04 mm
        x_dob_third = mm_to_points(32.53)
        y_dob_third = mm_to_points(297 - 60.04)  # Y-Koordinate von oben

        c.drawString(x_dob_third, y_dob_third, dob)

        # Platzieren der Pflegekasse auf der dritten Seite
        # X: 123,52 mm, Y: 43,90 mm
        x_insurance_third = mm_to_points(123.52)
        y_insurance_third = mm_to_points(297 - 43.90)  # Y-Koordinate von oben

        c.drawString(x_insurance_third, y_insurance_third, insurance)

        # Platzieren der Versichertennummer auf der dritten Seite
        # X: 138,32 mm, Y: 54,48 mm
        x_insurance_number_third = mm_to_points(138.32)
        y_insurance_number_third = mm_to_points(297 - 54.48)  # Y-Koordinate von oben

        c.drawString(x_insurance_number_third, y_insurance_number_third, insurance_number)

        # Platzieren des Pflegegrads auf der dritten Seite
        # X: 122,47 mm, Y: 50,52 mm
        x_pflegegrad_third = mm_to_points(122.47)
        y_pflegegrad_third = mm_to_points(297 - 50.52)  # Y-Koordinate von oben

        c.drawString(x_pflegegrad_third, y_pflegegrad_third, pflegegrad)

        # Automatisches Einfügen des aktuellen Datums
        # X: 4,23 mm, Y: 194,39 mm
        x_current_date = mm_to_points(4.23)
        y_current_date = mm_to_points(297 - 194.39)
        c.drawString(x_current_date, y_current_date, current_date)

        # Automatisches Einfügen der Unterschriftstexte
        # X: 50,26 mm, Y: 182,49 mm
        x_signature_line1 = mm_to_points(50.26)
        y_signature_line1 = mm_to_points(297 - 182.49)
        c.drawString(x_signature_line1, y_signature_line1, f"Die Unterschrift wurde am {current_date} von")

        # Zweite Zeile der Unterschrift
        x_signature_line2 = mm_to_points(50.26)
        y_signature_line2 = mm_to_points(297 - 186.00)  # leicht nach unten verschoben
        c.drawString(x_signature_line2, y_signature_line2, f"{name} getätigt.")

        c.save()

        # =============================================================
        # =============== PDF-SEITEN ZUSAMMENFÜGEN ====================
        # =============================================================
        writer = PdfWriter()

        # Erste Seite kombinieren
        with open(overlay_path_1, "rb") as overlay_file_1:
            overlay_reader_1 = PdfReader(overlay_file_1)
            overlay_page_1 = overlay_reader_1.pages[0]

            reader_1 = PdfReader(input_pdf_path_1)
            for page in reader_1.pages:
                page.merge_page(overlay_page_1)
                writer.add_page(page)

        # Zweite Seite kombinieren
        with open(overlay_path_2, "rb") as overlay_file_2:
            overlay_reader_2 = PdfReader(overlay_file_2)
            overlay_page_2 = overlay_reader_2.pages[0]

            reader_2 = PdfReader(input_pdf_path_2)
            for page in reader_2.pages:
                page.merge_page(overlay_page_2)
                writer.add_page(page)

        # Dritte Seite kombinieren
        with open(overlay_path_3, "rb") as overlay_file_3:
            overlay_reader_3 = PdfReader(overlay_file_3)
            overlay_page_3 = overlay_reader_3.pages[0]

            reader_3 = PdfReader(input_pdf_path_3)
            for page in reader_3.pages:
                page.merge_page(overlay_page_3)
                writer.add_page(page)

        # Finales PDF speichern
        with open(output_pdf_path, "wb") as output_file:
            writer.write(output_file)

        # Temporäre Overlay-Dateien löschen
        os.remove(overlay_path_1)
        os.remove(overlay_path_2)
        os.remove(overlay_path_3)

        return send_file(output_pdf_path, as_attachment=True)

    except Exception as e:
        return f"Fehler beim Verarbeiten der PDF: {str(e)}"

if __name__ == '__main__':


    app.run(debug=False, host='0.0.0.0')
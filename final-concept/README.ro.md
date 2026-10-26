> **Notă pentru acest repository:** acesta este documentul generatorului (V5). Designul salvat în Fusion ca **„final concept”** folosește aceleași piese (volume verificate identice), cu picioarele în altă poziție. Aici, `final-concept.f3d` / `final-concept.step` înlocuiesc `HX18-Inline-V5-Concept.f3d` / `.step`, iar `STL/` conține fișierele din `STL-BED-CONCEPT`.

# HX18 V5 — picior centrat, carcasă continuă

Revizie de formă și arhitectură după fotografia alb/roșu furnizată. Modelul actuatorului rămâne neales, conform deciziei din conversație. F3D-ul păstrează componentele, istoricul modelării și articulațiile Fusion. STEP transferă geometria, fără articulațiile Fusion. Nu este un ansamblu pregătit pentru fabricație.

## Ce s-a schimbat

Femurul are o singură carcasă continuă, cu spate alb și capac frontal roșu. Ambele rezervări de motor, pentru șold și genunchi, sunt în interiorul acesteia. Furcile axelor sunt bilaterale și intră în carcasă; tibia se îngustează simetric către o lamă centrată și talpă separată. Toate centrele cinematice ale piciorului au Y local zero. Nu există carcase de servo atașate în lateral ca în V4.

Motorul șoldului folosește montaj inversat: carcasa lui se mișcă împreună cu femurul, iar ieșirea se fixează de furca proximală. Această arhitectură ascunde corpul motorului, dar mută masă pe segmentul mobil. Cuplul necesar trebuie recalculat după alegerea actuatorului și masei finale. Este modelată o rezervare de carcasă de 32 × 27 × 13 mm, nu geometria unui model comercial confirmat. Urechile, spline-ul, horn-ul, rulmentul opus, mufele și cablurile reale rămân de definit.

| Referință geometrică | Valoare |
|---|---:|
| Raza axelor yaw | 49 mm |
| Legătura proximală | 45 mm |
| Axa șoldului la neutru | R94 mm, Z−12 mm |
| Femur între axe | 52 mm |
| Genunchi până la centrul tălpii | 93 mm |
| Femur, unghi absolut la neutru | +55° |
| Tibie, unghi absolut la neutru | −72° |
| Genunchi, unghi relativ la neutru | −127° |
| Carcasă superioară închisă, local | 80 × 37,4 × 28 mm |

Zero-ul joint-urilor Fusion este postura asamblată. Nu reprezintă centrul electric al unui servo. Punctul de referință al tălpii este `(93,0,0)` în tibie, nu contactul real cu solul.

Ansamblul are 27 de piese rigide și 6 tălpi, din 8 definiții de print, 18 articulații revolute și 47 legături rigide. Sunt modelate **12 șuruburi de service**: 4 pentru capacul corpului, 2 pentru caseta electronică și unul din spate pentru fiecare capac roșu. Șuruburile motorului/horn-ului, axele opuse, inserturile și montajul plăcilor sunt suplimentare și nefinalizate. 12 nu este numărul total de șuruburi al robotului funcțional.

Capacul roșu are o limbă de ghidare și rezervare de insert M3. Demontarea motorului necesită eliberarea prinderilor axelor, deoarece furcile interne împiedică extragerea directă a motorului. Nu este un mecanism de schimbare rapidă a servoului.

## Corp și electronice

Corpul păstrează cada structurală, capacul și caseta electronică demontabilă, aproximativ 144 × 126 mm în plan. Rezervările sunt: baterie 43 × 23 × 13 mm jos, regulator 34 × 44 × 10 mm la nivel intermediar și controler 52 × 24 × 8 mm deasupra. Sunt volume pentru organizare, nu plăci sau acumulatori aleși.

`KEEP-OUT` participă la verificarea coliziunilor, dar nu se printează. În imaginile piciorului izolat, rezervarea yaw poate apărea deoarece corpul central este ascuns pentru inspecție; în ansamblu aceasta se află în corp. Motorul șoldului și cel al genunchiului sunt în carcasă, nu ascunse doar prin dezactivarea vizibilității.

Alegerea ESP32, a driverelor pentru cele 18 canale, a alimentării, siguranței și cablurilor trebuie făcută cu actuatorul real. Spațiul pentru plăcile de comandă servo și conectorii acestora nu este confirmat. Firmware-ul V2 nu este validat pentru geometria V5.

Volumul CAD echivalent cu PLA complet solid este aproximativ **356 g**, fără tălpi. V4 avea aproximativ 316 g: închiderea și centrarea carcaselor adaugă aproximativ 40 g. Nu este masa măsurată a printului sau a robotului; motoarele, bateria, infill-ul, cablurile și hardware-ul schimbă rezultatul. Cuplul continuu și jocul transmisiei nu sunt validate, iar MG90S nu este confirmat pentru această arhitectură.

## Print și montaj

`STL-CONCEPT` conține geometria în coordonatele componentelor. `STL-BED-CONCEPT` conține copii rotite rigid și așezate la Z0, în milimetri; acestea propun o orientare, fără validarea suporturilor în slicer.

Integrarea furcii și a lamei într-o tibie reduce piesele, dar creează suprafețe suspendate. Tibia, furca proximală, carcasa superioară, capacul cu limbă proeminentă și unele zone ale capacului central pot necesita suporturi sau alte orientări. Alegerea PETG/PLA/PA, numărul de pereți și orientarea straturilor trebuie verificată printr-un picior fizic. Talpa necesită probă de material, toleranță și retenție. Modelul nu este declarat fără suporturi.

Nu începe printarea întregului robot înainte de alegerea motorului și definitivarea prinderilor sale. Primul prototip practic este un singur picior, cu cupon de potrivire pentru motorul real, prinderi pe ambele părți și probă de sarcină. Grosimea carcasei, degajările și găurile de pivot sunt provizorii.

## Verificări și sursă

`CAD-validation.json`: solide native, cantități, istoric și interferențe la neutru. `Motion-validation.json`: 71 de poziții discrete, graful articulațiilor, cinematică independentă și alinierea în plan. Limitele testate sunt yaw ±20°, hip ±12°, knee ±15° față de postura de referință; nu sunt limite de funcționare dovedite sub sarcină. Eșantionarea nu acoperă orice poziție intermediară sau traseu de mers.

`Archive-roundtrip.json`: redeschiderea F3D-ului efectiv exportat. `Mesh-validation.json`: închiderea STL-urilor, orientarea normalelor, un singur solid și concordanța volumului cu Fusion. `Python-validation.json`: teste și acoperire doar pentru modulele Python pure, separat de verificările native Fusion. Nu sunt validate rezistența, jocul transmisiei, mersul, cablurile, răcirea sau alimentarea.

Adaugă `Automation/HexapodV5` în Fusion Scripts and Add-Ins și rulează `HexapodV5`. Scriptul creează un document nou și directorul `generated`, fără să modifice sketch-ul original. Parametrii Fusion `hx_...` sunt referințe ale generatorului; modificarea lor în interfață nu regenerează automat dimensiunile numerice. Modifică sursa, reconstruiește și repetă verificările.

Testele pure: `python -m unittest discover -v` în directorul scriptului, cu numpy și trimesh instalate. Pentru analiza exporturilor: `python mesh_checks.py <directorul-rezultatelor>`. Aceste biblioteci nu sunt necesare pentru generarea CAD nativă în Fusion.

Direcția anterioară a pornit de la [ManufacturedMotion/Hex](https://github.com/ManufacturedMotion/Hex), iar această revizie urmărește fotografia alb/roșu furnizată ulterior. Geometria este construită separat; nu sunt incluse mesh-uri sau CAD copiate din proiectul de referință.

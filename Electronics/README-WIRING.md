# HX18 — electronica din corp, cablarea și prima pornire

Controlerul ales este **Adafruit Feather ESP32 V2 #5400**. Două plăci **Adafruit PCA9685 #815** generează cele 18 semnale pentru MG90S. Bateria alimentează două convertoare separate: **Pololu D42V110F5 #5671 pentru servouri**, **Pololu D24V10F5 #2831 pentru logică**. Deschide `wiring.svg` pentru schema vectorială și `BOM-electronics.csv` pentru componente.

Aceasta este configurația proiectată. Dimensiunile plăcilor și găurile au fost verificate în CAD-ul oficial; cablarea, curentul, temperatura, compatibilitatea semnalului de 3,3V și calibrarea celor 18 servouri necesită verificare pe componentele fizice. Niciun servo real nu a fost alimentat în timpul proiectării. Modelul CAD al componentelor reprezintă anvelopa nominală, fără garanția că mufele și firele cumpărate au exact aceeași formă.

## Piesele principale

| Cantitate | Componentă exactă | Rol / dimensiuni nominale |
|---:|---|---|
| 1 | Adafruit Feather ESP32 V2 #5400, fără header-e GPIO înalte | ESP32 cu USB-C; PCB 50,8 × 22,86 mm; masa publicată 6 g |
| 2 | Adafruit PCA9685 #815, rev C | 16 canale PWM pe placă; PCB CAD 62,23 × 25,4 mm; aproximativ 9 g cu conectori |
| 1 | Pololu D42V110F5 #5671 | 5V pentru servouri; 31,8 × 43,2 × 9 mm; 15 g |
| 1 | Pololu D24V10F5 #2831 | 5V / 1A nominal pentru Feather; 12,7 × 17,78 × 3,56 mm; 1 g |
| 1 | Gens ace Adventure GEA4502S60XT3 | LiPo 450mAh, 2S, 7,4V nominal, 60C; aproximativ 43 × 23 × 13 mm, 28 g; XT30 + G-Tech-3P |
| 18 | TowerPro MG90S | 13,4 g fiecare în specificația oficială; 241,2 g pentru toate cele 18 |

[Feather produs](https://www.adafruit.com/product/5400), [PCA produs](https://www.adafruit.com/product/815), [buck servouri](https://www.pololu.com/product/5671), [buck logică](https://www.pololu.com/product/2831/specs), [bateria exactă](https://gensace.de/fr/collections/product-download/products/gea4502s60xt3), [servo producător](https://towerpro.com.tw/product/mg90s-3/).

## Topologia de alimentare

1. **XT30 baterie → F1 siguranță provizorie 7A pe pozitiv → distribuție intrare.** Păstrează siguranța aproape de baterie și izolează complet conexiunile. Valoarea 7A este o țintă de proiectare, nu un cod de componentă cumpărată: alegerea fizică trebuie verificată după curentul măsurat și curba timp–curent. Nu monta automat 7,5A sau o siguranță mai mare fără această verificare.
2. Distribuția intrării alimentează VIN/GND ale ambelor convertoare. Include **D1, o mufă de deconectare fizică pe ramura de intrare a buck-ului pentru servouri**, accesibilă cu capacul montat. Buck-ul de logică poate rămâne alimentat pentru diagnostic. Mufa bateriei D0 rămâne deconectarea generală. Un întrerupător mecanic poate înlocui D1 numai dacă are o clasificare DC documentată pentru tensiunea și curentul ramurii. Nu presupune că un rating 10A la 125VAC reprezintă 10A la DC.
3. Ieșirea VOUT de 5V a buck-ului mare alimentează o **distribuție separată, în stea, pentru cele 18 servouri**. Firul roșu al fiecărui servo ajunge aici; firul maro ajunge la distribuția GND. Firele portocalii merg individual la pinii PWM de pe PCA9685. În această topologie **PCA V+ rămâne neconectat**: nu transportăm curentul tuturor servourilor prin traseele acestor plăci, al căror rating agregat nu este publicat în documentația consultată.
4. Ieșirea VOUT de 5V a buck-ului mic alimentează Feather printr-un **cablu scurt USB-C de alimentare**, cu VBUS/GND corect identificate. USB-C trebuie să fie un cablu sau un ansamblu de alimentare conform, nu pini conectați la întâmplare.
5. Toate GND sunt comune. Întoarcerea curentului servourilor merge direct la distribuția de putere, nu prin Feather sau prin cablul USB. Leagă separat GND Feather și GND celor două PCA la referința comună.

La distribuția de 5V pentru servouri pune inițial **două condensatoare electrolitice low-ESR de 1000µF / minimum 10V**, unul pentru fiecare bancă de nouă servouri, cu polaritatea corectă. Valoarea este o propunere inițială pentru teste: condensatorul amortizează un tranzient, nu înlocuiește un regulator capabil să livreze curentul. Montează-l într-un locaș separat; diametrul/înălțimea depind de produsul real. Fire recomandate inițial: silicon flexibil 18AWG pe traseele principale scurte, 22AWG pe ramurile către un singur picior, cu verificarea temperaturii și a căderii de tensiune la sarcina reală. Nu folosi o placă breadboard sau fire Dupont pentru alimentarea comună a celor 18 servouri.

Fiecare ramură, mufa, izolarea și siguranța trebuie dimensionate împreună. Bateria de 2S ajunge la **8,4V încărcată**: această tensiune se aplică doar intrării convertoarelor. Nu conecta 2S la servo, la PCA VCC sau la Feather BAT/JST. [Feather alimentare](https://learn.adafruit.com/adafruit-esp32-feather-v2/power-management-2), [Adafruit separarea logică/servouri](https://learn.adafruit.com/16-channel-pwm-servo-driver?view=all).

## Legăturile de logică

| Din Feather ESP32 V2 | Spre ambele PCA9685 |
|---|---|
| 3V, 3,3V | VCC |
| GND | GND |
| SDA / GPIO22 | SDA |
| SCL / GPIO20 | SCL |
| GPIO27 | OE, legate împreună |

Feather V2 are **SDA=22 și SCL=20**, conform plăcii alese. Nu copia GPIO21/22 din exemple pentru un ESP32 generic. Placa A păstrează jumperele de adresă deschise, **0x40**. Pe placa B închide numai A0, **0x41**. I²C are pull-up-uri la VCC, de aceea VCC este 3,3V. Ține firele I²C scurte și departe de alimentarea servourilor. Firmware-ul folosește magistrala la 100kHz.

**OE este activ LOW:** LOW pornește impulsurile, HIGH le dezactivează. Cele două PCA Adafruit au fiecare pull-down OE de 10kΩ. Montează **o rezistență comună de 1kΩ, 1%, între OE și Feather 3V**, păstrând rezistențele de pe plăci. Cele două pull-down-uri sunt 5kΩ în paralel, astfel încât nivelul implicit este aproximativ 2,75V la alimentare de 3,3V. Un pull-up comun de 10kΩ peste pull-down-urile existente nu produce nivelul HIGH necesar. Alternativa de îndepărtare a R7 și folosire a unui pull-up 10kΩ schimbă ansamblul și trebuie documentată dacă este aleasă.

Măsoară OE cu Feather în reset și PCA alimentate: trebuie HIGH. Dacă se pierde alimentarea Feather, se pierde și 3,3V pentru PCA: **nu trata această condiție ca o garanție electrică de oprire a unui servo care mai are 5V**. Folosește D1/D0 pentru oprire fizică. La eroare I²C, timeout sau reset, firmware-ul dezactivează semnalele; răspunsul MG90S la lipsa semnalului trebuie verificat. Susține corpul: lipsa cuplului îl poate lăsa să cadă. [Pinii Feather](https://learn.adafruit.com/adafruit-esp32-feather-v2/pinouts), [PCA9685 NXP](https://www.nxp.com/docs/en/data-sheet/PCA9685.pdf).

## Exact care servo intră unde

Numerele sunt cele din CAD și firmware, în jurul corpului: **L1=0°, L2=60°, L3=120°, L4=180°, L5=240°, L6=300°**. Fiecare picior are YAW/coxa, HIP/femur, KNEE/tibia. Indicii comenzilor pornesc de la zero.

| Picior | Servo YAW | Servo HIP | Servo KNEE | PCA / canale PWM |
|---|---:|---:|---:|---|
| L1 | 0 | 1 | 2 | A 0x40 / 0,1,2 |
| L2 | 3 | 4 | 5 | A 0x40 / 3,4,5 |
| L3 | 6 | 7 | 8 | A 0x40 / 6,7,8 |
| L4 | 9 | 10 | 11 | B 0x41 / 0,1,2 |
| L5 | 12 | 13 | 14 | B 0x41 / 3,4,5 |
| L6 | 15 | 16 | 17 | B 0x41 / 6,7,8 |

Canalele 9–15 ale ambelor plăci rămân dezactivate. Etichetează ambele capete ale fiecărui cablu, de exemplu `L2-HIP / A-CH4 / servo4`. Dacă folosești prelungitoare/adaptoare JR, separă alimentarea în adaptor: numai firul de semnal ajunge la pinul PWM de pe PCA; roșu/maro ajung la distribuția externă. Nu conecta o mufă servo completă la PCA și o alimentare externă contradictorie în același timp. Culorile obișnuite MG90S sunt maro=GND, roșu=+, portocaliu=semnal, dar verifică unitățile tale.

## Programare, fără alimentări care se luptă între ele

Pentru Upload, deconectează bateria D0 și cablul USB-C alimentat de buck; apoi conectează Feather la computer prin USB-C. În Arduino IDE selectează **Adafruit Feather ESP32 V2**, pachetul **esp32 by Espressif Systems 3.x**, și deschide `HX18Controller/HX18Controller.ino` din pachetul Firmware. Setările sunt în `config.h`.

Pentru teste pe banc poți ține Feather alimentat prin computer, cu cablul logic de la buck deconectat, iar sursa de servouri separată, cu GND comun. Cablarea de logică rămâne ca mai sus. Oprește și deconectează sursa înainte de modificarea firelor. Firmware-ul furnizat blochează `ARM` până când toate cele 18 calibrări sunt marcate fizic verificate. Consola `serial_console.py` trimite heartbeat; un monitor serial obișnuit fără `PING` periodic va produce timeout după aproximativ 1,5s. Nu lăsa robotul să se sprijine doar pe cuplul servourilor în aceste teste.

## Prima pornire și calibrare

1. Cu bateria deconectată verifică continuitatea, polaritatea și absența scurtului pe fiecare rail. Inspectează lipiturile și izolația. Pentru prima alimentare folosește sursă de laborator cu limitare de curent, în limita VIN a convertoarelor.
2. Fără servouri conectate măsoară buck servo aproximativ 5V, buck logic aproximativ 5V, VCC PCA 3,3V. Verifică temperaturile, adresele 0x40/0x41, OE și forma impulsurilor la osciloscop/analizor logic. Regulatorul servo specifică 5V ±3%; confirmă și tensiunea minimă la mufa servo sub sarcină.
3. Măsoară frecvența fiecărei PCA și ajustează separat `oscillatorHz[0]` și `[1]`. Pentru PRE_SCALE=121: `oscillatorHz = frecvența PWM măsurată × 4096 × 122`. Măsoară un canal activ în BENCH, apoi marchează separat `oscillatorVerified[0]` și `[1]` în `true`; ARM este blocat și fără aceste două confirmări. Nominal 50Hz, PRE_SCALE=121 la 25MHz produce aproximativ 50,03Hz; pasul de timp este aproximativ 4,88µs. CAD-ul nu calibrează un oscilator real.
4. Conectează **un servo**, cu horn-ul demontat și robotul susținut. Rulează consola cu heartbeat și trimite `DISARM`, `BENCH_ACK`, `BENCH 0`. Numai canalul zero este activ, la centru nominal 1500µs. Primul impuls către un servo cu poziție necunoscută poate provoca o mișcare rapidă; demontarea horn-ului elimină sarcina mecanică inițială.
5. `STEP 5` / `STEP -5` comandă numai o fereastră inițială ±50µs și viteza redusă; nu măsoară capetele servo-ului. `DISARM` înainte să muți horn-ul sau cablul. Repetă pentru `BENCH 1` până la `BENCH 17`, câte unul.
6. Montează horn-urile în referința CAD neutră: femur −25° absolut, tibia −95° absolut, deci KNEE relativ −70°. Determină fizic pentru fiecare canal `centerUs`, `usPerDegree`, `offsetDegrees`, `sign`, `minimumUs`, `maximumUs`. Valorile furnizate `sign=+1` și 1200–1800µs sunt nevalidate și nu presupun că toate unitățile sunt identice. Verifică marginile de mișcare fără frecare/opriri mecanice, apoi marchează `verified=true` individual și `calibrationReviewed=true` numai după toate verificările.
7. Reîncarcă configurația. Din neutral fizic, **cu ansamblul suspendat și corpul susținut**, trimite `CAL_ACK`, `ARM`. Rampa inițială de 5s mută toate picioarele din neutral în postura compactă; această tranziție de prototip nu este o ridicare verificată de la sol și nu trebuie făcută cu picioarele încărcate. Așteaptă `READY` și verifică postura sub sprijin progresiv. `WALK` începe prin 18s de prepoziționare, ridicând un singur picior pe rând și ținând celelalte fixe; apoi pornește mersul lent și crește viteza corpului gradual în 3s. `STOP` păstrează XY ale picioarelor plantate și coboară piciorul aflat în aer în 2s; nu trage toate picioarele spre stand. `DISARM` elimină impulsurile. D1 întrerupe fizic alimentarea servourilor.
8. Treci de la un picior la ansamblul suspendat, apoi la sprijin progresiv pe masă. Înregistrează curentul mediu/vârf, căderea de tensiune, temperatura după 1/5/10 minute, vibrațiile și slăbirea șuruburilor. Potrivirea mecanică și bucla de software nu constituie dovada că MG90S suportă masa finală.

Detaliile comenzilor și modelului sunt în `Firmware/README.md`. Monitorizarea bateriei este **dezactivată în firmware-ul livrat**; nu există un divizor rezistiv instalat fictiv și nu există o protecție hardware de subtensiune livrată. Pentru mers pe baterie trebuie folosit un monitor/protector potrivit 2S, verificat pe fiecare celulă; nu te baza pe limita de dropout a buck-ului ca protecție LiPo. Prima verificare poate fi făcută pe sursă de laborator.

## Curentul și ce poate promite proiectul

TowerPro publică 1,8kgf·cm la 4,8V, aproximativ 0,1765N·m, **cuplu de blocare**, nu cuplu continuu permis. Masa oficială este 13,4g/servo. Producătorul nu publică un curent de blocare MG90S în pagina consultată. Valorile 0,6–1,0A pe servo sunt **ipoteze pentru dimensionare**, nu măsurători; pentru 18 unități dau 10,8–18A. Mersul, sprijinul și servourile cumpărate pot schimba mult curentul. Metalul din angrenaj nu face servo-ul imun la blocare sau încălzire.

Pololu #5671 publică un curent continuu tipic maxim de **8–15A**, dependent de VIN și răcire; „11A” este valoarea de comparație la VIN=42V. Verifică graficul și temperatura reală la 6,6–8,4V, în carcasa finală. Nu presupunem că poate alimenta 18 servouri blocate simultan. Dacă măsurătorile depășesc capacitatea, configurația trebuie revizuită, de exemplu două rail-uri independente pentru nouă servouri; **nu lega pozitiv ieșirile a două buck-uri în paralel** fără proiect specific pentru împărțirea curentului. [Specificația regulatorului](https://www.pololu.com/product/5671).

Siguranța F1 de intrare **nu limitează curentul ieșirii la 7A**. Relația aproximativă este `Iieșire ≈ VIN × Iintrare × eficiență / 5V`. Cu 7A intrare și 90% eficiență, rezultă aproximativ 8,3A la VIN=6,6V sau 10,6A la VIN=8,4V, înainte de consumul logicii. Siguranța se deschide după o curbă timp–curent; nu este un limitator electronic precis. Mufa fizică întrerupe alimentarea, dar nu monitorizează automat curentul. [Littelfuse despre siguranțe](https://www.littelfuse.com/assetdocs/automotive-passenger-car-catalog?assetguid=613475c5-28ce-4646-a46e-0a9344b7a944).

La 450mAh × 7,4V, bateria are nominal 3,33Wh. Cu ipoteza 80% energie utilizabilă și 90% eficiență, autonomia ilustrativă este aproximativ 5,8 minute la 25W sau 14,4 minute la 10W, înainte de logică. Nu este o autonomie măsurată. Rating-ul 60C de pe baterie nu demonstrează curentul disponibil în ansamblul nostru.

## Așezare și cabluri în corp

Păstrează bateria centrală, joasă și detașabilă. Folosește o curea cu protecție între pouch și plastic; lasă ieșirea XT30/G-Tech accesibilă. Scoate bateria pentru încărcare cu un încărcător **2S LiPo balance** și cablurile compatibile, departe de robot; portul USB al Feather nu încarcă acest pack. Verifică polaritatea și compatibilitatea G-Tech-3P, fără adaptoare presupuse din poze.

În layout-ul CAD V2, PCA-urile au axa lungă pe X, centrele Y=±16mm și fundul PCB la Z=21mm. Header-ele de servo sunt orientate spre exteriorul Y, aproximativ Y=21–29mm și Y=−21–−29mm. Podul electronicii începe la Z=38mm, Feather are fundul PCB la Z=44,4mm, iar capacul ajunge la Z=55mm. Aceste cote descriu layout-ul proiectat; nu sunt măsurători ale unui robot asamblat.

**Folosește Feather #5400 fără header-e GPIO înalte.** Leagă GPIO/3V/GND prin fire scurte lipite direct și izolate; un rând înalt de header-e plus mufe Dupont nu este inclus în gabaritul capacului. Pentru PCA, legăturile de logică pot fi lipite pe pad-uri sau terminate cu conectori realmente scunzi; bornele de putere V+ rămân neconectate în topologia cu distribuție externă. Accesul USB-C trebuie păstrat pentru mufa reală. STEMMA QT poate fi folosit doar dacă alimentarea sa comutată este configurată corect; schema principală folosește pad-urile SDA/SCL/3V ale Feather.

Anvelopa conectorului PCA ajunge la aproximativ 10,09mm deasupra fundului PCB și 2,01mm dedesubt; mufa servo conectată și cotul firului cer spațiu suplimentar. Evită să prinzi cabluri între podul Feather și plăci. **Condensatoarele de 1000µF și distribuția de putere nu au corpuri fizice modelate în CAD**: fixează-le în harness, în exteriorul zonelor de mișcare, după măsurarea componentelor reale. Nu considera un spațiu gol din CAD drept o dovadă că un condensator cumpărat încape acolo.

Regulatorul mare ocupă nominal Z=−1…8mm, deasupra raftului de putere Z=−6…−3mm, cu distanțiere izolatoare de 2mm; are componente și sub PCB, deci verifică și lipiturile. Buck-ul de logică are nominal Z=40,4…43,96mm, într-un locaș separat pe pod, X=±8,89mm, Y=15,15…27,85mm. Păstrează ventilația și separarea termică de baterie. Lasă bucle de serviciu pentru articulații și puncte de strain-relief; verifică toate pozițiile înainte de mers.

Găuri oficiale, în mm, față de colțul stânga-jos al PCB:

| Placă | Dimensiune PCB | Centre găuri / diametru |
|---|---|---|
| Feather | 50,8 × 22,86 | (2,54;2,54), (2,54;20,32), (48,26;2,54), (48,26;20,32); Ø2,5/2,54 |
| PCA rev C | 62,23 × 25,4 | (3,175;3,175), (3,175;22,225), (59,055;3,175), (59,055;22,225); Ø2,5 |
| Pololu #5671, orientare x=31,75/y=43,18 | 31,75 × 43,18 | (2,159;2,159), (27,559;2,159), (2,159;41,021), (27,559;41,021); Ø2,18 |

Pentru găurile plăcilor folosește M2 cu șaibe/izolare și lungime verificată; M3 nu intră în Ø2,5. Toleranța printului și grosimea distanțierului se verifică pe cupon. [CAD Feather oficial](https://github.com/adafruit/Adafruit-ESP32-Feather-V2-PCB), [CAD PCA oficial](https://github.com/adafruit/Adafruit-16-Channel-PWM-Servo-Driver-PCB), [desen Pololu oficial](https://www.pololu.com/file/0J2217/d42v110fx-step-down-voltage-regulator-dimensions.pdf), [modele Adafruit oficiale](https://github.com/adafruit/Adafruit_CAD_Parts).

## Cum rămâne împărțită validarea

- **Verificat din documentație/CAD:** modelul exact al plăcilor, adresele, pinii, găurile, anvelopele nominale și rolul OE.
- **Verificat software separat:** generarea țintelor și stările de control, în limitele raportului Firmware.
- **De verificat fizic înainte de funcționare:** unitățile MG90S reale, nivelul semnalului de 3,3V, calibrarea, alimentarea, siguranța, protecția bateriei, temperatura, masa totală, sprijinul și mersul.

Lista CSV marchează separat produsele exacte și consumabilele alese după specificație. Nu au fost cumpărate componente, trimise comenzi către servicii sau modificate conturi externe.

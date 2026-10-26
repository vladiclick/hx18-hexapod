# Verificare HX18 V2

Model CAD, firmware și fișiere printabile verificate separat. Nu au fost făcute teste pe servouri reale, imprimări, măsurări de curent sau probe de mers fizic.

- 154 instanțe;18revolute și134rigide; un singur ground și graf conectat fără cicluri.
- Nicio problemă de timeline și nicio interferență solidă în repaus.
- 133 configurații de articulații, inclusiv limite și picioare vecine, fără coliziuni;798 comparații CAD/FK.
- 254 cadre din mers/prepoziționare, plus extremele exacte ale unghiurilor, fără coliziuni. Intervale și hash-uri CSV în Gait-validation.json. Joint-urile Fusion rotunjesc la0,1°; eroarea maximă față de țintele firmware: 0.1514mm, limită de verificare0,3mm. FK pentru unghiurile efectiv aplicate verificat separat.
-17STL: solide închise, un singur corp conectat, normale consistente, mm, Zmin0 și volum apropiat de BRep.
-F3D final redeschis: geometrie, joint-uri, axe,17definiții printabile și sketch original păstrate.
-18teste de matematică/layout:100%linii în geometry.py și core_layout.py. Aceasta nu este acoperirea întregului generator Fusion; generatorul este verificat prin auditul CAD și export/redeschidere.
-Firmware: compilare reală pentru esp32:esp32:adafruit_feather_esp32_v2, core3.3.12. Teste ASan/UBSan + integrare/E2E simulate;100%linii și92,77%ramuri în nucleul matematic. Review final independent: fără constatări blocante.

Păstrează distincția: eșantioanele nu dovedesc absența coliziunilor în orice mișcare continuă; modelul de contact software nu măsoară forța reală; anvelopele PCB nu validează cabluri/mufe comerciale; cuplul stall nu este cuplu continuu. Calibrarea fizică individuală este obligatorie înainte de ARM.

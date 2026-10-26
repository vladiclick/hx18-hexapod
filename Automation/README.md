# Generator și verificare HX18 V2

STL-urile livrate sunt deja orientate. Pentru utilizarea modelului nu este necesar să rulezi generatorul.

Generatorul Fusion este local, fără conturi externe sau servicii CAD. În Fusion → Utilities → Scripts and Add-Ins → Add script from device, selectează folderul HexapodV2. Rulează HexapodV2 pentru reconstruire din Original-Sketch.f3d; creează un document nou, cu originalul păstrat ca referință. Fișierele se exportă în folderul V2. Parametrii hx_* sunt cote de referință, fără legare automată a tuturor sketch-urilor.

După o reconstruire, exportul nativ STL este în coordonatele componentelor, iar plăcile Y trebuie reorientate. Rulează orient_exported_stl.py **o singură dată, imediat după export proaspăt**, cu Python+numpy+trimesh. Nu îl rula peste STL-urile deja orientate din acest pachet.

Teste matematice: din HexapodV2, `python3 -m unittest discover -p 'test_*.py'`. Cu coverage instalat: `coverage run --source=geometry,core_layout -m unittest discover -p 'test_*.py'`, apoi `coverage report`. Rezultatul livrat:18teste,100%linii doar în cele două module matematice.

cad_audit.py verifică133poziții în Fusion. cad_gait_audit.py verifică CSV-urile din Firmware cu extrema exactă a fiecărui unghi inclusă. Fusion rotunjește comenzile la0,1°; auditul verifică FK pentru unghiurile aplicate și separat eroarea față de CSV. cad_finish.py exportă/redeschide arhiva și produce vederi. Aceste module necesită contextul Python al Fusion, nu Python obișnuit. Fișierele de mod din Automation/logs sunt pentru depanarea generatorului; nu sunt necesare la reconstruirea normală.

verify_stl.py face numai validare și nu schimbă fișierele. Testele firmware sunt separate în Firmware. Rapoartele livrate validează modelul final, fără a garanta componentele fizice cumpărate.
